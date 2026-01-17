"""
DBOS Workflow Communication Examples

This server demonstrates three communication patterns for workflows:
1. WORKFLOW EVENTS - Publish key-value pairs that clients can query
2. WORKFLOW MESSAGING - Send/receive messages to/from workflows
3. WORKFLOW STREAMING - Stream real-time data from workflows to clients

BLOCKING BEHAVIOR SUMMARY:
- DBOS.get_event(): Blocks the CLIENT request until event is available (server can handle other requests)
- DBOS.recv_async(): Suspends the WORKFLOW (not server) until message arrives (use await in async workflows!)
- DBOS.send(): NON-BLOCKING - queues message immediately and returns
- DBOS.read_stream(): NON-BLOCKING - returns all current stream values immediately
- DBOS.write_stream(): NON-BLOCKING - writes to stream and continues

Key takeaway: The server never blocks! Clients and individual workflows may wait, but the
server always remains responsive to handle new requests.
"""

import logging
import time
from contextlib import asynccontextmanager

import psutil
import uvicorn
from dbos import DBOS, DBOSConfig, Queue, SetWorkflowID, WorkflowHandleAsync
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s ->> %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


# Constants for workflow communication
PROGRESS_EVENT = "progress"
STATUS_EVENT = "status"
RESULT_EVENT = "result"
NOTIFICATION_TOPIC = "notification"
STREAM_KEY = "progress_stream"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config: DBOSConfig = {
        "name": "dbos-starter",
        "system_database_url": "postgresql://trustle:trustle@localhost:5432/test_dbos_sys?sslmode=disable",
        "run_admin_server": False,
        "enable_otlp": False,
    }
    DBOS(config=config)
    DBOS.launch()
    logger.info("Application started")

    yield

    # Shutdown
    logger.info("FastAPI shutdown event triggered")
    logger.info("Initiating graceful shutdown of DBOS...")
    DBOS.destroy(workflow_completion_timeout_sec=10)
    logger.info("Graceful shutdown complete")


app = FastAPI(lifespan=lifespan)

queue = Queue("example-queue")


async def fibonacci(n: int) -> int:
    """Calculate Fibonacci number recursively (CPU-intensive)"""
    if n <= 1:
        return n
    return await fibonacci(n - 1) + await fibonacci(n - 2)


@app.get("/health")
async def health_check():
    """Health check endpoint to monitor memory usage
    I run this: `while true; do http localhost:8000/health; sleep 1; done`
    or `while true; do echo -n "$(date +"%T") - "; http localhost:8000/health | jq '.memory_mb'; sleep 1; done`
    in another terminal to see memory usage over time.
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024  # Convert bytes to MB
    return {
        "status": "ok",
        "memory_mb": round(memory_mb, 2),
    }


@DBOS.step(retries_allowed=True)
async def dbos_step(n: int) -> dict:
    DBOS.logger.info(f"Starting Fibonacci calculation for n={n}")
    # Run CPU-intensive work in thread pool to avoid blocking
    result = await fibonacci(n)
    DBOS.logger.info(f"Fibonacci({n}) = {result}")
    return {"n": n, "fibonacci": result}


# ============================================================================
# EXAMPLE 1: WORKFLOW EVENTS
# Events allow workflows to publish key-value pairs that clients can retrieve
# ============================================================================


@DBOS.workflow()
async def workflow_with_events(n_steps: int) -> list[dict]:
    """
    Workflow that publishes events at different stages.
    Clients can query these events to know the workflow progress.
    """
    workflow_id = DBOS.workflow_id
    DBOS.logger.info(f"Starting workflow_with_events {workflow_id} with {n_steps} steps")

    # Set initial status event
    DBOS.set_event(STATUS_EVENT, "started")
    DBOS.set_event(PROGRESS_EVENT, 0)

    step_results = []
    base_number = 28

    for i in range(n_steps):
        # Update progress event before each step
        progress_pct = int((i / n_steps) * 100)
        DBOS.set_event(PROGRESS_EVENT, progress_pct)
        DBOS.set_event(STATUS_EVENT, f"processing_step_{i + 1}")

        result = await dbos_step(base_number + i)
        step_results.append(result)

    # let's sum all fibonacci results
    total = sum(r["fibonacci"] for r in step_results)

    # Set completion events
    DBOS.set_event(PROGRESS_EVENT, 100)
    DBOS.set_event(STATUS_EVENT, "completed")
    DBOS.set_event(RESULT_EVENT, {"total_steps": n_steps, "total_fibonacci": total})

    DBOS.logger.info(f"Workflow {workflow_id} completed")
    return step_results


@app.post("/start-workflow-events/{workflow_id}/{n_steps}")
async def start_workflow_events(workflow_id: str, n_steps: int):
    """
    Start a workflow that publishes events.
    Use GET /workflow-events/{workflow_id}/{event_key} to query events.
    """
    # Start the workflow in the background
    with SetWorkflowID(workflow_id):
        await DBOS.start_workflow_async(workflow_with_events, n_steps)

    return {
        "workflow_id": workflow_id,
        "message": "Workflow started with events",
        "query_endpoints": {
            "progress": f"/workflow-events/{workflow_id}/progress",
            "status": f"/workflow-events/{workflow_id}/status",
            "result": f"/workflow-events/{workflow_id}/result",
            "all_events": f"/workflow-events/{workflow_id}/all",
        },
    }


@app.get("/workflow-events/{workflow_id}/all")
async def get_all_workflow_events(workflow_id: str):
    """
    Retrieve all events published by a workflow.
    """
    events = DBOS.get_all_events(workflow_id)
    return {"workflow_id": workflow_id, "events": events}


@app.get("/workflow-events/{workflow_id}/{event_key}")
async def get_workflow_event(workflow_id: str, event_key: str, timeout: int = 5):
    """
    Retrieve a specific event from a workflow.
    This will wait up to 'timeout' seconds for the event to be published.

    BLOCKING BEHAVIOR:
    - This endpoint blocks the client (not the server) until the event is available or timeout expires.
    - The server can handle other requests concurrently while this waits.
    """
    # DBOS.get_event() blocks this request handler but doesn't block the event loop
    event_value = DBOS.get_event(workflow_id, event_key, timeout_seconds=timeout)

    if event_value is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_key}' not found or timeout reached")

    return {"workflow_id": workflow_id, "event_key": event_key, "value": event_value}


# ============================================================================
# EXAMPLE 2: WORKFLOW MESSAGING AND NOTIFICATIONS
# Workflows can receive messages from external sources
# ============================================================================


@DBOS.workflow()
async def workflow_with_messaging(n_steps: int) -> dict:
    """
    Workflow that can receive messages/notifications from external sources.
    It will wait for an approval message before proceeding with processing.
    Messages are automatically queued by DBOS, so they can be sent even
    before the workflow starts executing.
    """
    workflow_id = DBOS.workflow_id
    DBOS.logger.info(f"Starting workflow_with_messaging {workflow_id}")
    # BLOCKING BEHAVIOR:
    # recv_async() suspends THIS WORKFLOW (not the server or event loop) until a message arrives
    # or the timeout expires. The server continues handling other requests normally.
    # Messages are queued in the database, so they can be sent even before this line executes.
    # Wait for approval notification (with 60 second timeout)
    # Note: Messages sent via DBOS.send() are queued, so this will receive
    # messages even if they were sent before this line executes.
    # IMPORTANT: Use recv_async() in async workflows to avoid blocking the event loop
    DBOS.logger.info("Waiting for approval notification...")
    approval = await DBOS.recv_async(topic=NOTIFICATION_TOPIC, timeout_seconds=60)

    if approval is None or not approval.get("approved"):
        DBOS.logger.warning(f"Workflow {workflow_id} not approved or timed out")
        return {
            "status": "cancelled",
            "reason": "Not approved or timeout",
            "results": [],
        }

    DBOS.logger.info(f"Workflow {workflow_id} approved, proceeding with processing")

    # Process steps
    step_results = []
    base_number = 10

    for i in range(n_steps):
        result = await dbos_step(base_number + i)
        step_results.append(result)

    return {"status": "completed", "results": step_results}


@app.post("/start-workflow-messaging/{workflow_id}/{n_steps}")
async def start_workflow_messaging(workflow_id: str, n_steps: int):
    """
    Start a workflow that waits for a message/notification.
    Use POST /send-message/{workflow_id} to send approval.

    Note: Messages are automatically queued by DBOS, so you can send
    messages immediately after this endpoint returns. The workflow
    will receive them when it calls recv().
    """
    DBOS.logger.info(f"Endpoint: Starting workflow {workflow_id}")

    # Start the workflow in the background
    with SetWorkflowID(workflow_id):
        await DBOS.start_workflow_async(workflow_with_messaging, n_steps)

    DBOS.logger.info(f"Endpoint: Workflow {workflow_id} started successfully")
    return {
        "workflow_id": workflow_id,
        "message": "Workflow started and will wait for approval notification",
        "send_approval": f"/send-message/{workflow_id}",
        "note": "Send POST request with JSON body: {'approved': true}. Messages are queued automatically.",
    }


@app.post("/send-message/{workflow_id}")
async def send_message_to_workflow(workflow_id: str, message: dict):
    """
    Send a message/notification to a running workflow.
    Example body: {"approved": true, "message": "Go ahead!"}

    BLOCKING BEHAVIOR:
    - This endpoint does NOT block. It immediately queues the message in the database and returns.
    - The message will be delivered to the workflow when it calls recv_async().
    """
    DBOS.logger.info(f"Endpoint: Sending message to workflow {workflow_id}: {message}")
    # DBOS.send() is non-blocking - it queues the message in the database and returns immediately
    DBOS.send(workflow_id, message, topic=NOTIFICATION_TOPIC)
    DBOS.logger.info(f"Endpoint: Message sent successfully to workflow {workflow_id}")

    return {
        "workflow_id": workflow_id,
        "message": "Notification sent to workflow",
        "payload": message,
    }


# ============================================================================
# EXAMPLE 3: WORKFLOW STREAMING
# Workflows can stream real-time data to clients
# ============================================================================


@DBOS.workflow()
async def workflow_with_streaming(n_steps: int) -> list[dict]:
    """
    Workflow that streams progress updates in real-time.
    Clients can read the stream to get live updates.
    """
    workflow_id = DBOS.workflow_id
    DBOS.logger.info(f"Starting workflow_with_streaming {workflow_id}")

    # Write initial stream message
    DBOS.write_stream(
        STREAM_KEY,
        {
            "timestamp": time.time(),
            "type": "start",
            "message": f"Workflow started with {n_steps} steps",
        },
    )

    step_results = []
    base_number = 10

    for i in range(n_steps):
        # Stream progress before each step
        DBOS.write_stream(
            STREAM_KEY,
            {
                "timestamp": time.time(),
                "type": "progress",
                "step": i + 1,
                "total_steps": n_steps,
                "message": f"Starting step {i + 1}/{n_steps}",
            },
        )

        result = await dbos_step(base_number + i)
        step_results.append(result)

        # Stream result after each step
        DBOS.write_stream(
            STREAM_KEY,
            {
                "timestamp": time.time(),
                "type": "result",
                "step": i + 1,
                "result": result,
            },
        )

    # Stream completion message
    DBOS.write_stream(
        STREAM_KEY,
        {
            "timestamp": time.time(),
            "type": "complete",
            "message": "Workflow completed successfully",
            "total_results": len(step_results),
        },
    )

    # Close the stream
    DBOS.close_stream(STREAM_KEY)

    DBOS.logger.info(f"Workflow {workflow_id} completed")
    return step_results


@app.post("/start-workflow-streaming/{workflow_id}/{n_steps}")
async def start_workflow_streaming(workflow_id: str, n_steps: int):
    """
    Start a workflow that streams real-time updates.
    Use GET /workflow-stream/{workflow_id} to read the stream.
    """
    # Start the workflow in the background
    with SetWorkflowID(workflow_id):
        await DBOS.start_workflow_async(workflow_with_streaming, n_steps)

    return {
        "workflow_id": workflow_id,
        "message": "Workflow started with streaming",
        "read_stream": f"/workflow-stream/{workflow_id}",
    }


@app.get("/workflow-stream/{workflow_id}")
async def read_workflow_stream(workflow_id: str):
    """
    Read all values from a workflow's stream.
    This returns all streamed values in order.

    BLOCKING BEHAVIOR:
    - This endpoint does NOT block. It immediately returns all messages currently in the stream.
    - Clients can poll this endpoint repeatedly to get new messages as they arrive.
    """
    stream_values = []

    try:
        # DBOS.read_stream() is NON-BLOCKING - returns immediately with all messages written so far
        for value in DBOS.read_stream(workflow_id, STREAM_KEY):
            stream_values.append(value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading stream: {str(e)}")

    return {
        "workflow_id": workflow_id,
        "stream_values": stream_values,
        "total_messages": len(stream_values),
    }


# ============================================================================
# ORIGINAL ENDPOINTS
# ============================================================================


@DBOS.workflow(max_recovery_attempts=2)
async def dbos_workflow(n_steps: int) -> list[dict]:
    DBOS.logger.info(f"Starting workflow with {n_steps} Fibonacci calculations")
    step_results = []
    # Calculate Fibonacci for numbers 10, 11, 12, etc.
    base_number = 10
    for i in range(n_steps):
        result = await dbos_step(base_number + i)
        step_results.append(result)
    DBOS.logger.info("Workflow completed")
    return step_results


@app.get("/")
@DBOS.workflow(max_recovery_attempts=2)
async def dbos_root_workflow():
    DBOS.logger.info("Starting root workflow")
    handles = []
    # Enqueue 5 workflows, each calculating 1-5 Fibonacci numbers
    for i in range(1, 6):
        handle: WorkflowHandleAsync = await queue.enqueue_async(dbos_workflow, i)
        handles.append(handle)

    # Return handle statuses without blocking
    statuses = [await handle.get_status() for handle in handles]
    DBOS.logger.info("Root workflow completed")
    return {"status": "completed", "handles_status": statuses}


DBOS.launch()

# run with: python main2.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
