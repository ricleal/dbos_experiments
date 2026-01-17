# Quick Reference: DBOS Workflow Communication

## Quick Start

```bash
# Terminal 1: Start server
python server.py

# Terminal 2: Run tests
python test_communication.py

# Or run client examples
python example_client_lib.py
```

## ⚠️ Blocking Behavior Quick Reference

| Operation | Location | Blocks? | Duration |
|-----------|----------|---------|----------|
| `GET /workflow-events/{id}/{key}` | Client | ✅ YES | Until event available or timeout |
| `GET /workflow-stream/{id}` | Client | ❌ NO | Returns immediately |
| `POST /send-message/{id}` | Client | ❌ NO | Returns immediately |
| `DBOS.get_event()` | Server Endpoint | ✅ YES | Until event available or timeout |
| `DBOS.read_stream()` | Server Endpoint | ❌ NO | Returns immediately |
| `DBOS.send()` | Server Endpoint | ❌ NO | Returns immediately |
| `DBOS.set_event()` | Workflow | ❌ NO | Publishes immediately |
| `DBOS.write_stream()` | Workflow | ❌ NO | Writes immediately |
| `await DBOS.recv_async()` | Async Workflow | ✅ YES | Until message or timeout |
| `DBOS.recv()` | Sync Workflow | ✅ YES | Until message or timeout |

### ⚠️ Critical: Use recv_async() in Async Workflows!

```python
# ❌ WRONG - Blocks event loop
@DBOS.workflow()
async def bad_workflow():
    msg = DBOS.recv(topic="approval")  # Blocks entire event loop!

# ✅ CORRECT
@DBOS.workflow()
async def good_workflow():
    msg = await DBOS.recv_async(topic="approval")  # Properly async
```

## API Endpoints Summary

### 1. Events Endpoints

```bash
# Start workflow with events
POST /start-workflow-events/{workflow_id}/{n_steps}

# Get specific event
GET /workflow-events/{workflow_id}/{event_key}?timeout=5

# Get all events
GET /workflow-events/{workflow_id}/all
```

**Example:**
```bash
curl -X POST http://localhost:8000/start-workflow-events/my-wf-1/3
curl http://localhost:8000/workflow-events/my-wf-1/progress
curl http://localhost:8000/workflow-events/my-wf-1/all
```

### 2. Messaging Endpoints

```bash
# Start workflow that waits for messages
POST /start-workflow-messaging/{workflow_id}/{n_steps}

# Send message to workflow
POST /send-message/{workflow_id}
Content-Type: application/json
Body: {"approved": true, "message": "..."}
```

**Example:**
```bash
curl -X POST http://localhost:8000/start-workflow-messaging/my-wf-2/3
curl -X POST http://localhost:8000/send-message/my-wf-2 \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### 3. Streaming Endpoints

```bash
# Start workflow with streaming
POST /start-workflow-streaming/{workflow_id}/{n_steps}

# Read stream
GET /workflow-stream/{workflow_id}
```

**Example:**
```bash
curl -X POST http://localhost:8000/start-workflow-streaming/my-wf-3/5
curl http://localhost:8000/workflow-stream/my-wf-3
```

## Code Patterns

### Pattern 1: Publishing Events (Workflow → Client)

```python
@DBOS.workflow()
async def my_workflow():
    # Publish events that clients can query
    DBOS.set_event("status", "processing")
    DBOS.set_event("progress", 50)
    DBOS.set_event("result", {"data": "..."})
```

### Pattern 2: Receiving Messages (Client → Workflow)

```python
@DBOS.workflow()
async def my_workflow():
    # Wait for external notification
    message = DBOS.recv(topic="notification", timeout_seconds=60)
    if message and message.get("approved"):
        # Proceed with processing
        ...
```

### Pattern 3: Streaming Updates (Workflow → Client)

```python
@DBOS.workflow()
async def my_workflow():
    # Stream real-time updates
    DBOS.write_stream("logs", {"msg": "Starting..."})
    DBOS.write_stream("logs", {"msg": "Processing..."})
    DBOS.write_stream("logs", {"msg": "Done!"})
    DBOS.close_stream("logs")
```

## When to Use Each Mechanism

| Use Case | Mechanism | Why |
|----------|-----------|-----|
| Progress bar / percentage | **Events** | Need latest value only |
| Payment webhook | **Messaging** | External system sends notification |
| Live log viewer | **Streaming** | Need complete history of updates |
| Status indicator | **Events** | Simple key-value lookup |
| Human approval | **Messaging** | Workflow waits for input |
| LLM token streaming | **Streaming** | Real-time sequential data |
| Dashboard metrics | **Events** | Polling for latest values |
| Multi-step approval | **Messaging** | Interactive workflow |
| Data pipeline logs | **Streaming** | Detailed audit trail |

## Quick Troubleshooting

### Events
- ❌ Event not found → Workflow hasn't set it yet or wrong key
- ✅ Solution: Increase timeout or check workflow status

### Messaging  
- ❌ Workflow not receiving message → Wrong topic or workflow ID
- ✅ Solution: Verify topic name matches exactly (case-sensitive)

### Streaming
- ❌ Empty stream → Workflow hasn't started streaming yet
- ✅ Solution: Wait or check workflow hasn't failed

## Python Client Usage

```python
from dbos import DBOSClient
import os

client = DBOSClient(
    system_database_url=os.environ["DBOS_SYSTEM_DATABASE_URL"]
)

# Events
events = client.get_all_events("workflow-id")
progress = client.get_event("workflow-id", "progress", timeout_seconds=5)

# Messaging
client.send("workflow-id", {"approved": True}, topic="notification")

# Streaming
for msg in client.read_stream("workflow-id", "stream-key"):
    print(msg)
```

## Testing Checklist

- [ ] Server is running on port 8000
- [ ] Database connection is working
- [ ] Can start workflow with events
- [ ] Can query events (progress, status, result)
- [ ] Can start workflow with messaging
- [ ] Can send approval message to workflow
- [ ] Can start workflow with streaming
- [ ] Can read stream values

## Common Workflow Patterns

### Pattern: Multi-stage Process with Progress

```python
@DBOS.workflow()
async def data_pipeline():
    stages = ["extract", "transform", "load"]
    for i, stage in enumerate(stages):
        DBOS.set_event("stage", stage)
        DBOS.set_event("progress", int((i+1) / len(stages) * 100))
        await process_stage(stage)
```

### Pattern: Approval Gate

```python
@DBOS.workflow()
async def approval_workflow(order_id):
    # Process order
    order = await process_order(order_id)
    
    # Wait for manager approval
    approval = DBOS.recv(topic="approval", timeout_seconds=3600)
    
    if approval and approval.get("approved"):
        await fulfill_order(order)
    else:
        await cancel_order(order)
```

### Pattern: Live Progress Updates

```python
@DBOS.workflow()
async def batch_processor(items):
    total = len(items)
    for i, item in enumerate(items):
        DBOS.write_stream("progress", {
            "item": i+1,
            "total": total,
            "item_id": item.id
        })
        await process_item(item)
    DBOS.close_stream("progress")
```

## Performance Tips

1. **Events**: Perfect for polling (low overhead)
2. **Messaging**: Use for infrequent notifications only
3. **Streaming**: Can grow large, consider pagination for long-running workflows

## Next Steps

1. Try the test script: `python test_communication.py`
2. Explore client examples: `python client_examples.py`
3. Build your own workflow with communication
4. Read full docs: https://docs.dbos.dev/python/tutorials/workflow-communication
