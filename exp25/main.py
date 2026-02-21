import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

import httpx
import uvicorn
from dbos import DBOS, DBOSConfig, Queue, SetEnqueueOptions, WorkflowHandle, WorkflowStatus
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -> %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP request logs from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Define the three queues with different rate limiters
# Queue for users: 2 requests every 1 second
queue_users = Queue(
    "queue_users",
    partition_queue=True,
    concurrency=1,
    limiter={"limit": 2, "period": 1},
)

# Queue for groups: 2 requests every 5 seconds
queue_groups = Queue(
    "queue_groups",
    partition_queue=True,
    concurrency=1,
    limiter={"limit": 2, "period": 5},
)

# Queue for permissions: 3 requests every 10 seconds
queue_permissions = Queue(
    "queue_permissions",
    partition_queue=True,
    concurrency=1,
    limiter={"limit": 3, "period": 10},
)

# Type definitions
Provider = Literal["aws", "azure", "gcp"]
DataType = Literal["users", "groups", "permissions"]

HTTPBIN_URL = "http://localhost:8080"

# Track start times for each provider/data_type combination to show relative timing
_start_times: dict[tuple[Provider, DataType], float] = {}


def get_queue_for_data_type(data_type: DataType) -> Queue:
    """Return the appropriate queue based on data type."""
    if data_type == "users":
        return queue_users
    elif data_type == "groups":
        return queue_groups
    elif data_type == "permissions":
        return queue_permissions
    else:
        raise ValueError(f"Unknown data type: {data_type}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config: DBOSConfig = {
        "name": "exp25-multiple-queues",
        "system_database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        "run_admin_server": False,
        "application_version": "0.1.0",
        "executor_id": "exp25-executor-1",
        "enable_otlp": False,
    }
    DBOS(config=config)
    DBOS.launch()

    yield

    # Shutdown
    DBOS.destroy(workflow_completion_timeout_sec=30)
    logger.info("✅ Graceful shutdown complete")


app = FastAPI(lifespan=lifespan)


@DBOS.step()
def make_http_request(
    provider: Provider,
    data_type: DataType,
    request_num: int,
) -> dict:
    """Make a real HTTP request to httpbin to simulate API call."""
    # Track start time for this provider/data_type combination
    key = (provider, data_type)
    if key not in _start_times:
        _start_times[key] = time.time()

    # Calculate elapsed time from first request in this combination
    elapsed_from_start = time.time() - _start_times[key]

    # Get queue name for context
    queue_name = get_queue_for_data_type(data_type).name

    # Log the request with elapsed time from first request
    logger.info(
        f"[{queue_name:18s}] [{provider.upper():5s}][{data_type:11s}] Request #{request_num} - {elapsed_from_start:6.2f}s"
    )

    # Make actual HTTP request to httpbin
    endpoint = f"{HTTPBIN_URL}/get"

    try:
        response = httpx.get(endpoint, timeout=2.0)
        return {"status_code": response.status_code}
    except Exception as e:
        logger.error(f"[{queue_name:18s}] [{provider.upper():5s}][{data_type:11s}] Request #{request_num} ✗ {e}")
        raise


def generic_process_data_request(
    provider: Provider,
    data_type: DataType,
    n_requests: int,
) -> list[WorkflowStatus]:
    logger.info(f"🚀 Starting workflow for [{provider.upper()}][{data_type}] with {n_requests} requests")
    results = []
    queue = get_queue_for_data_type(data_type)
    for i in range(n_requests):
        with SetEnqueueOptions(queue_partition_key=provider):
            result = queue.enqueue(
                make_http_request,
                provider=provider,
                data_type=data_type,
                request_num=i + 1,
            )
            status = result.get_status()
            results.append(status)
    return results


@DBOS.workflow(max_recovery_attempts=2)
def aws_process_data_request(
    data_type: DataType,
    n_requests: int,
) -> list[WorkflowStatus]:
    return generic_process_data_request("aws", data_type, n_requests)


@DBOS.workflow(max_recovery_attempts=2)
def azure_process_data_request(
    data_type: DataType,
    n_requests: int,
) -> list[WorkflowStatus]:
    return generic_process_data_request("azure", data_type, n_requests)


@DBOS.workflow(max_recovery_attempts=2)
def gcp_process_data_request(
    data_type: DataType,
    n_requests: int,
) -> list[WorkflowStatus]:
    return generic_process_data_request("gcp", data_type, n_requests)


@app.get("/provider/{provider}/data_type/{data_type}")
def enqueue_requests(provider: Provider, data_type: DataType, n: int = 5):
    """
    Enqueue n requests for a specific provider and data type.

    Example: GET /provider/aws/data_type/users?n=10
    This will enqueue 10 requests to the users queue with AWS as partition key.
    """
    logger.info(f"📨 Enqueuing {n} requests for [{provider.upper()}][{data_type}]")

    try:
        match provider:
            case "aws":
                workflow_handle: WorkflowHandle = DBOS.start_workflow(
                    aws_process_data_request,
                    data_type=data_type,
                    n_requests=n,
                )
            case "azure":
                workflow_handle: WorkflowHandle = DBOS.start_workflow(
                    azure_process_data_request,
                    data_type=data_type,
                    n_requests=n,
                )
            case "gcp":
                workflow_handle: WorkflowHandle = DBOS.start_workflow(
                    gcp_process_data_request,
                    data_type=data_type,
                    n_requests=n,
                )
            case _:
                raise ValueError(f"Unknown provider: {provider}")

        workflow_status = workflow_handle.get_status()

        status = workflow_status.status if workflow_status else "unknown"
        return {
            "status": "success",
            "provider": provider,
            "data_type": data_type,
            "workflow_id": workflow_handle.workflow_id,
            "workflow_status": status,
            "queue_name": get_queue_for_data_type(data_type).name,
            "rate_limit": get_queue_for_data_type(data_type).limiter,
        }

    except Exception as e:
        logger.error(f"❌ Failed to enqueue requests for [{provider.upper()}][{data_type}]: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/demo")
def demo():
    """Demo endpoint to enqueue a mix of requests for testing."""
    # Clear start times for a fresh demo
    _start_times.clear()

    providers = ["aws", "azure", "gcp"]
    data_types = ["users", "groups", "permissions"]

    for provider in providers:
        for data_type in data_types:
            n_requests = 5
            match provider:
                case "aws":
                    DBOS.start_workflow(
                        aws_process_data_request,
                        data_type=data_type,
                        n_requests=n_requests,
                    )
                case "azure":
                    DBOS.start_workflow(
                        azure_process_data_request,
                        data_type=data_type,
                        n_requests=n_requests,
                    )
                case "gcp":
                    DBOS.start_workflow(
                        gcp_process_data_request,
                        data_type=data_type,
                        n_requests=n_requests,
                    )

    return {"status": "demo started"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
