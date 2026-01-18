# DBOS Workflow Communication Patterns

This experiment demonstrates three powerful communication patterns for DBOS workflows:

1. **Workflow Events** - Publish key-value pairs that clients can query
2. **Workflow Messaging** - Send/receive messages to/from workflows  
3. **Workflow Streaming** - Stream real-time data from workflows to clients

## Overview

The server implements three different workflows, each showcasing a distinct communication pattern. These patterns enable building interactive, real-time applications with durable execution guarantees.

### Key Concepts

**Blocking Behavior Summary:**
- `DBOS.get_event()`: Blocks the CLIENT request until event available (server handles other requests)
- `DBOS.recv_async()`: Suspends the WORKFLOW until message arrives (server remains responsive)
- `DBOS.send()`: NON-BLOCKING - queues message immediately and returns
- `DBOS.read_stream()`: Returns current stream values immediately (polling-friendly)
- `DBOS.write_stream()`: NON-BLOCKING - writes to stream and continues

**Important:** The server never blocks! Individual client requests and workflows may wait, but the server always remains responsive to handle new requests.

## Setup

### Prerequisites

```bash
# Install required packages
pip install dbos fastapi uvicorn psutil httpie

# Ensure PostgreSQL is running and accessible
# Default connection: postgresql://trustle:trustle@localhost:5432/test_dbos_sys
```

### Start the Server

```bash
cd exp23
python server.py
```

The server starts on `http://localhost:8000` with endpoints for all three communication patterns.

## Communication Patterns

### 1. Workflow Events

Events store the **latest value** for each key. Perfect for status tracking and progress monitoring.

**Use Cases:**
- Progress percentages (0%, 25%, 50%, 100%)
- Status indicators (started, processing, completed)
- Final results or summaries

**How it Works:**
- Workflows publish events with `DBOS.set_event(key, value)`
- Clients query events with `DBOS.get_event(workflow_id, key)`
- Each key stores only the **most recent value**
- Get requests can block until event is available (with timeout)

**Run the Example:**

```bash
# Make executable and run
chmod +x commands_events.sh
./commands_events.sh

# Or manually:
# Start workflow
http POST http://localhost:8000/start-workflow-events/my-workflow-1/10

# Query specific event (waits up to 5 seconds)
http GET http://localhost:8000/workflow-events/my-workflow-1/progress

# Get all events at once
http GET http://localhost:8000/workflow-events/my-workflow-1/all
```

**Event Types Demonstrated:**
- `progress` - Percentage complete (0-100)
- `status` - Current workflow state (started, processing_step_X, completed)
- `result` - Final workflow results

### 2. Workflow Messaging

Messages enable **one-time delivery** of notifications to workflows. Perfect for approval flows and interactive workflows.

**Use Cases:**
- Approval workflows (wait for user approval)
- Notifications and alerts
- Workflow coordination and handoffs

**How it Works:**
- External systems send messages with `DBOS.send(workflow_id, message, topic)`
- Workflows receive messages with `DBOS.recv_async(topic, timeout)`
- Messages are **queued in the database** - can be sent before workflow starts
- Each message is delivered exactly once

**Run the Example:**

```bash
# Make executable and run
chmod +x commands_messaging.sh
./commands_messaging.sh

# Or manually:
# Start workflow (waits for approval)
http POST http://localhost:8000/start-workflow-messaging/my-workflow-2/5

# Send approval message
http POST http://localhost:8000/send-message/my-workflow-2 approved:=true message="Approved!"
```

**Message Flow:**
1. Workflow starts and begins waiting for approval
2. External system sends approval message (or rejection)
3. Workflow receives message and proceeds or cancels accordingly
4. Messages persist in database - guaranteed delivery even if workflow restarts

### 3. Workflow Streaming

Streams provide **full message history** in order. Perfect for logs, real-time monitoring, and LLM token streaming.

**Use Cases:**
- LLM token streaming (real-time AI responses)
- Build/deployment logs
- Progress monitoring with detailed steps
- Audit trails

**How it Works:**
- Workflows write to streams with `DBOS.write_stream_async(key, value)`
- Clients read streams with `DBOS.read_stream(workflow_id, key)`
- All messages are stored in order (complete history)
- Streams can be read multiple times while workflow is running
- Close stream with `DBOS.close_stream_async(key)` when done

**Run the Example:**

```bash
# Make executable and run
chmod +x commands_streaming.sh
./commands_streaming.sh

# Or manually:
# Start workflow
http POST http://localhost:8000/start-workflow-streaming/my-workflow-3/10

# Poll stream repeatedly (returns current snapshot)
http GET http://localhost:8000/workflow-stream/my-workflow-3
# Wait a moment and poll again to see new messages
sleep 2
http GET http://localhost:8000/workflow-stream/my-workflow-3
```

**Stream Message Types:**
- `start` - Workflow initialization
- `progress` - Step-by-step progress updates
- `result` - Step completion with results
- `complete` - Workflow completion

**Polling Pattern:**
The endpoint returns immediately with all messages written so far. Clients can poll repeatedly to get new messages as they arrive. Each poll returns the complete history, allowing clients to track progress in real-time.

## Comparison Table

| Feature | Events | Messaging | Streaming |
|---------|--------|-----------|-----------|
| **Storage** | Latest value only | One-time delivery | Full history |
| **Use Case** | Status, progress % | Approvals, notifications | Logs, monitoring |
| **Reading** | Query by key | Receive in workflow | Poll for updates |
| **Blocking** | Client waits for value | Workflow waits for message | Non-blocking reads |
| **Example** | Progress: 75% | Approval: true | Step 1 done, Step 2 done... |

## Implementation Details

### WorkflowEvent Enum

The server uses an enum for type-safe event keys:

```python
class WorkflowEvent(str, Enum):
    PROGRESS = "progress"
    STATUS = "status"
    RESULT = "result"
```

### Async Considerations

- Use `recv_async()` in async workflows to avoid blocking the event loop
- Use `write_stream_async()` and `close_stream_async()` in async workflows
- The server uses asyncio with FastAPI for full async support

### Stream Reading Strategy

The stream endpoint uses a timeout-based approach to read only current values:

```python
async with asyncio.timeout(0.1):
    async for value in DBOS.read_stream_async(workflow_id, STREAM_KEY):
        stream_values.append(value)
```

This allows the endpoint to return quickly with current values rather than blocking until the stream closes.

## Testing

Each test script (`commands_*.sh`) includes:
- Server availability check
- Unique workflow ID generation
- Step-by-step demonstration with explanations
- Summary of key concepts

Run all tests:

```bash
./commands_events.sh
./commands_messaging.sh
./commands_streaming.sh
```

## Key Takeaways

1. **Server Never Blocks**: All operations are non-blocking from the server's perspective
2. **Client Blocking**: Only client requests block (waiting for events/messages)
3. **Workflow Blocking**: Only individual workflows block (waiting for messages)
4. **Durability**: All communication persists in the database
5. **Recovery**: Workflows can be interrupted and resumed without losing communication state

## Architecture

```
┌─────────────┐
│   Client    │ ←── Events (query latest values)
│  (HTTP/CLI) │ ←── Stream (poll for updates)
└──────┬──────┘ ──→ Messages (send notifications)
       │
       ↓
┌─────────────┐
│ FastAPI     │ ←── Non-blocking request handlers
│  Server     │ ←── Concurrent request processing
└──────┬──────┘
       │
       ↓
┌─────────────┐
│    DBOS     │ ←── Durable execution
│  Workflows  │ ←── Event/message/stream storage
└──────┬──────┘ ←── Workflow recovery
       │
       ↓
┌─────────────┐
│ PostgreSQL  │ ←── Persistent storage
│  Database   │ ←── ACID guarantees
└─────────────┘
```

## Further Reading

- [DBOS Workflows Documentation](https://docs.dbos.dev)
- [Workflow Communication Patterns](https://docs.dbos.dev/api-reference/contexts#workflow-communication)
- [FastAPI Async Support](https://fastapi.tiangolo.com/async/)

## Notes

- Fibonacci calculations are used as CPU-intensive example steps
- Base numbers configured for demonstration purposes (manageable execution times)
- Memory monitoring available via `/health` endpoint
- All workflows use async/await for proper event loop integration
