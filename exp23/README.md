# DBOS Workflow Communication Examples

This example demonstrates all three workflow communication mechanisms in DBOS:
1. **Workflow Events** - Publish key-value pairs that clients can query
2. **Workflow Messaging** - Send notifications to running workflows
3. **Workflow Streaming** - Stream real-time data from workflows

## Quick Start

```bash
# Terminal 1: Start the server
python server.py

# Terminal 2: Run comprehensive tests
python test_communication.py

# Or run client examples
python example_client_lib.py
```

## ⚠️ Important: Understanding Blocking Behavior

### Client-Side Blocking (HTTP Requests)
- **Events**: `GET /workflow-events/{workflow_id}/{event_key}` **BLOCKS** until event is available or timeout expires (default 60s)
- **Streaming**: `GET /workflow-stream/{workflow_id}` **DOES NOT BLOCK** - returns immediately with current stream content
- **Messaging**: `POST /send-message/{workflow_id}` **DOES NOT BLOCK** - returns immediately after queuing message

### Server-Side Blocking (Endpoint Handlers)
- **Events**: Endpoint blocks while calling `DBOS.get_event()` (waits for event with timeout)
- **Streaming**: Endpoint does NOT block - `DBOS.read_stream()` returns immediately
- **Messaging**: Endpoint does NOT block - `DBOS.send()` queues message and returns

### Workflow-Side Blocking (Inside Workflows)
- **Events**: `DBOS.set_event()` **DOES NOT BLOCK** - publishes immediately
- **Streaming**: `DBOS.write_stream()` **DOES NOT BLOCK** - writes immediately
- **Messaging**: `await DBOS.recv_async()` **BLOCKS** until message received or timeout (must use `recv_async` in async workflows!)

### Critical: recv() vs recv_async()
⚠️ **In async workflows, ALWAYS use `await DBOS.recv_async()`, NOT `DBOS.recv()`**

- ❌ `DBOS.recv()` in async workflow → **Blocks entire event loop** for up to 60+ seconds!
- ✅ `await DBOS.recv_async()` → Properly awaits without blocking event loop

```python
# ❌ WRONG - Blocks event loop
@DBOS.workflow()
async def bad_workflow():
    msg = DBOS.recv(topic="approval")  # BLOCKS EVERYTHING!

# ✅ CORRECT - Properly async
@DBOS.workflow()
async def good_workflow():
    msg = await DBOS.recv_async(topic="approval")  # Non-blocking await
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for API endpoints and code patterns.

## Setup

Start the server:
```bash
python server.py
```

## Example 1: Workflow Events

Events allow workflows to publish status information that clients can retrieve.

### Start a workflow with events:
```bash
# Start workflow with ID "wf-events-1" that will run 3 steps
curl -X POST http://localhost:8000/start-workflow-events/wf-events-1/3
```

### Query specific events:
```bash
# Get progress (0-100%)
curl http://localhost:8000/workflow-events/wf-events-1/progress

# Get current status
curl http://localhost:8000/workflow-events/wf-events-1/status

# Get final result (will wait until workflow completes)
curl http://localhost:8000/workflow-events/wf-events-1/result

# Get all events at once
curl http://localhost:8000/workflow-events/wf-events-1/all
```

### Use Cases:
- Progress tracking (e.g., "Processing 45% complete")
- Status updates (e.g., "Validating data", "Processing payment")
- Returning intermediate results while workflow is running
- Building interactive UIs that show real-time progress

---

## Example 2: Workflow Messaging and Notifications

Workflows can wait for external notifications before proceeding.

### Start a workflow that waits for approval:
```bash
# Start workflow with ID "wf-msg-1" that will run 3 steps
curl -X POST http://localhost:8000/start-workflow-messaging/wf-msg-1/3
```

### Send approval notification:
```bash
# Approve the workflow
curl -X POST http://localhost:8000/send-message/wf-msg-1 \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "message": "Approved by admin"}'

# Or reject/cancel
curl -X POST http://localhost:8000/send-message/wf-msg-1 \
  -H "Content-Type: application/json" \
  -d '{"approved": false, "reason": "Rejected"}'
```

### Check the workflow result:
```bash
# Using DBOS CLI (if available)
dbos workflow get wf-msg-1

# Or query the workflow status via your own status endpoint
```

### Use Cases:
- Human-in-the-loop workflows (manual approval steps)
- Payment confirmations from external webhooks
- Waiting for external system responses
- Multi-step processes requiring user interaction

---

## Example 3: Workflow Streaming

Workflows can stream real-time updates as they execute.

### Start a workflow with streaming:
```bash
# Start workflow with ID "wf-stream-1" that will run 5 steps
curl -X POST http://localhost:8000/start-workflow-streaming/wf-stream-1/5
```

### Read the stream (while workflow is running or after):
```bash
# Get all streamed messages
curl http://localhost:8000/workflow-stream/wf-stream-1
```

Example output:
```json
{
  "workflow_id": "wf-stream-1",
  "stream_values": [
    {
      "timestamp": 1705500000.123,
      "type": "start",
      "message": "Workflow started with 5 steps"
    },
    {
      "timestamp": 1705500001.456,
      "type": "progress",
      "step": 1,
      "total_steps": 5,
      "message": "Starting step 1/5"
    },
    {
      "timestamp": 1705500002.789,
      "type": "result",
      "step": 1,
      "result": {"n": 30, "fibonacci": 832040}
    },
    ...
  ],
  "total_messages": 15
}
```

### Use Cases:
- Real-time progress monitoring with detailed logs
- Streaming LLM responses token-by-token
- Live data processing pipelines
- Long-running jobs with intermediate results
- Building dashboards with live updates

---

## Comparison of Communication Mechanisms

| Feature | Events | Messaging | Streaming |
|---------|--------|-----------|-----------|
| **Direction** | Workflow → Client | Client → Workflow | Workflow → Client |
| **Data Structure** | Key-value pairs | Messages with topics | Ordered sequence |
| **Latest Value** | ✓ Yes | ✗ No | ✗ No |
| **History** | ✗ No (only latest) | ✗ No | ✓ Yes (all values) |
| **Real-time** | ✓ Yes | ✓ Yes | ✓ Yes |
| **Best For** | Status/progress | Notifications/approvals | Logs/live updates |

---

## Testing All Three Together

Here's a complete test scenario:

```bash
# Terminal 1: Start the server
python server.py

# Terminal 2: Test Events
curl -X POST http://localhost:8000/start-workflow-events/wf-test-events/3
sleep 2
curl http://localhost:8000/workflow-events/wf-test-events/all

# Terminal 2: Test Messaging
curl -X POST http://localhost:8000/start-workflow-messaging/wf-test-msg/3
# Workflow is now waiting for approval...
sleep 1
curl -X POST http://localhost:8000/send-message/wf-test-msg \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# Terminal 2: Test Streaming
curl -X POST http://localhost:8000/start-workflow-streaming/wf-test-stream/5
sleep 3
curl http://localhost:8000/workflow-stream/wf-test-stream
```

---

## Advanced Usage

### Events with Timeout
```bash
# Wait up to 10 seconds for an event (default is 5)
curl "http://localhost:8000/workflow-events/wf-events-1/result?timeout=10"
```

### Using from Python Client

```python
from dbos import DBOSClient
import os

client = DBOSClient(system_database_url=os.environ["DBOS_SYSTEM_DATABASE_URL"])

# Read events
events = client.get_all_events("wf-events-1")
print(events)

# Send message
client.send("wf-msg-1", {"approved": True}, topic="notification")

# Read stream
for value in client.read_stream("wf-stream-1", "progress_stream"):
    print(value)
```

---

## Architecture Notes

- **Events**: Best for polling-based UIs where you want the latest status
- **Messaging**: Best for webhook-based integrations and approval flows
- **Streaming**: Best for detailed logging and real-time dashboards

All three mechanisms are:
- ✅ **Durable** - Persisted in the database
- ✅ **Recoverable** - Survive workflow interruptions
- ✅ **Reliable** - Guaranteed delivery and ordering

---

## Common Patterns

### Pattern 1: Progress Bar UI
```python
# Use Events for a simple progress indicator
while True:
    progress = get_event(workflow_id, "progress")
    if progress == 100:
        break
    update_ui_progress_bar(progress)
    sleep(1)
```

### Pattern 2: Payment Confirmation
```python
# Use Messaging for external webhook integration
@app.post("/payment-webhook/{workflow_id}")
def payment_webhook(workflow_id: str, payment_status: str):
    DBOS.send(workflow_id, {"status": payment_status}, topic="payment")
```

### Pattern 3: Live Log Viewer
```python
# Use Streaming for a real-time log viewer
for log_entry in DBOS.read_stream(workflow_id, "logs"):
    display_log(log_entry)
```

---

## Troubleshooting

### Event not found
- Make sure the workflow has executed past the point where it sets the event
- Check that the event key matches exactly
- Increase the timeout parameter

### Message not received
- Verify the workflow ID is correct
- Check that the topic matches (case-sensitive)
- Ensure the workflow hasn't timed out its recv() call

### Stream is empty
- Workflow might not have started streaming yet
- Check that STREAM_KEY matches
- Verify workflow hasn't failed before streaming

---

## Next Steps

Try building:
1. A dashboard that polls events every second to show live progress
2. A webhook endpoint that sends approval messages from external systems
3. A log viewer that displays streaming output in real-time

For more details, see: https://docs.dbos.dev/python/tutorials/workflow-communication
