# Exp23: DBOS Workflow Communication - Complete Implementation

## Overview

This experiment implements and demonstrates all three DBOS workflow communication mechanisms:

1. **Workflow Events** - Key-value pairs for status/progress tracking
2. **Workflow Messaging** - Notifications and approvals from external sources
3. **Workflow Streaming** - Real-time data streaming with full history

## Files in This Experiment

### Core Implementation
- **`server.py`** - FastAPI server with all three communication mechanisms implemented
  - Events endpoints: Start workflows that publish events, query events
  - Messaging endpoints: Start workflows that wait for messages, send messages
  - Streaming endpoints: Start workflows that stream data, read streams

### Testing & Examples
- **`test_communication.py`** - Comprehensive automated test suite
  - Tests all three mechanisms sequentially
  - Validates functionality and correctness
  - Provides timing and output examples
  
- **`client_examples.py`** - Reusable client library with usage examples
  - `WorkflowClient` class for easy integration
  - Example functions for each mechanism
  - Combined usage examples

### Documentation
- **`README.md`** - Main documentation with detailed examples
  - Complete API reference
  - Command-line examples with curl
  - Use cases and patterns
  - Comparison matrix
  
- **`QUICK_REFERENCE.md`** - Quick lookup guide
  - API endpoints summary
  - Code patterns
  - When to use each mechanism
  - Troubleshooting tips
  
- **`VISUAL_GUIDE.md`** - Visual explanations with diagrams
  - Architecture overview
  - Sequence diagrams for each mechanism
  - Decision tree for choosing the right mechanism
  - Real-world scenarios

- **`PROJECT_SUMMARY.md`** - This file, project overview

## Critical: Blocking Behavior Summary

### Client HTTP Requests
- ✅ **BLOCKS**: `GET /workflow-events/{id}/{key}` (waits for event with timeout)
- ❌ **NO BLOCK**: `GET /workflow-stream/{id}` (returns immediately)
- ❌ **NO BLOCK**: `POST /send-message/{id}` (returns immediately)

### Server Endpoints
- ✅ **BLOCKS**: Event endpoints calling `DBOS.get_event()` (waits with timeout)
- ❌ **NO BLOCK**: Stream endpoints calling `DBOS.read_stream()` (immediate)
- ❌ **NO BLOCK**: Message endpoints calling `DBOS.send()` (immediate)

### Inside Workflows
- ❌ **NO BLOCK**: `DBOS.set_event()` - publishes immediately
- ❌ **NO BLOCK**: `DBOS.write_stream()` - writes immediately
- ✅ **BLOCKS**: `await DBOS.recv_async()` - waits for message (use in async workflows!)
- ✅ **BLOCKS**: `DBOS.recv()` - waits for message (use in sync workflows only!)

### ⚠️ CRITICAL: recv() vs recv_async()
**Always use `await DBOS.recv_async()` in async workflows!**

```python
# ❌ WRONG - Blocks entire event loop for 60+ seconds!
@DBOS.workflow()
async def bad_workflow():
    msg = DBOS.recv(topic="approval")

# ✅ CORRECT - Properly async
@DBOS.workflow()
async def good_workflow():
    msg = await DBOS.recv_async(topic="approval")
```

## Getting Started

### Prerequisites
```bash
# Make sure you have DBOS installed
pip install dbos

# PostgreSQL should be running
# Update connection string in server.py if needed
```

### Quick Start
```bash
# Terminal 1: Start the server
cd /home/leal/git/dbos_experiments/exp23
python server.py

# Terminal 2: Run tests
python test_communication.py

# Or try client examples
python example_client_lib.py
```

### Manual Testing
```bash
# Test Events
curl -X POST http://localhost:8000/start-workflow-events/test-wf-1/3
curl http://localhost:8000/workflow-events/test-wf-1/progress
curl http://localhost:8000/workflow-events/test-wf-1/all

# Test Messaging
curl -X POST http://localhost:8000/start-workflow-messaging/test-wf-2/3
curl -X POST http://localhost:8000/send-message/test-wf-2 \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# Test Streaming
curl -X POST http://localhost:8000/start-workflow-streaming/test-wf-3/5
sleep 5
curl http://localhost:8000/workflow-stream/test-wf-3
```

## Architecture

```
┌─────────────────────────────────────┐
│         Client Application          │
│  (curl, Python client, Web UI)      │
└──────────────┬──────────────────────┘
               │ HTTP REST API
┌──────────────▼──────────────────────┐
│         FastAPI Server              │
│  - Events endpoints                 │
│  - Messaging endpoints              │
│  - Streaming endpoints              │
└──────────────┬──────────────────────┘
               │ DBOS API
┌──────────────▼──────────────────────┐
│         DBOS Runtime                │
│  - Workflow execution               │
│  - State management                 │
│  - Recovery & reliability           │
└──────────────┬──────────────────────┘
               │ SQL
┌──────────────▼──────────────────────┐
│      PostgreSQL Database            │
│  - Workflow state                   │
│  - Events, messages, streams        │
└─────────────────────────────────────┘
```

## Key Features Demonstrated

### 1. Workflow Events
- ✅ Publishing progress updates (0-100%)
- ✅ Publishing status changes
- ✅ Publishing results
- ✅ Querying specific events with timeout
- ✅ Querying all events at once

### 2. Workflow Messaging
- ✅ Workflows waiting for external notifications
- ✅ Sending messages to running workflows
- ✅ Topic-based message routing
- ✅ Approval/rejection flows
- ✅ Timeout handling

### 3. Workflow Streaming
- ✅ Real-time progress streaming
- ✅ Multi-stage workflow updates
- ✅ Timestamped messages
- ✅ Structured message types
- ✅ Stream closing

## Code Patterns Implemented

### Events Pattern
```python
@DBOS.workflow()
async def workflow_with_events(n_steps: int):
    DBOS.set_event("status", "started")
    DBOS.set_event("progress", 0)
    # ... process steps ...
    DBOS.set_event("progress", 100)
    DBOS.set_event("result", final_result)
```

### Messaging Pattern
```python
@DBOS.workflow()
async def workflow_with_messaging(n_steps: int):
    # Wait for approval
    approval = DBOS.recv(topic="notification", timeout_seconds=60)
    if approval and approval.get("approved"):
        # Process approved workflow
        ...
```

### Streaming Pattern
```python
@DBOS.workflow()
async def workflow_with_streaming(n_steps: int):
    DBOS.write_stream("progress", {"msg": "Starting..."})
    for step in steps:
        DBOS.write_stream("progress", {"step": step})
    DBOS.close_stream("progress")
```

## Testing Coverage

| Test | Status | Description |
|------|--------|-------------|
| Events - Start workflow | ✅ | Start workflow with unique ID |
| Events - Poll progress | ✅ | Query progress event during execution |
| Events - Get status | ✅ | Query status event |
| Events - Get result | ✅ | Query result event after completion |
| Events - Get all | ✅ | Query all events at once |
| Messaging - Start workflow | ✅ | Start workflow that waits |
| Messaging - Send approval | ✅ | Send approval message |
| Messaging - Timeout handling | ✅ | Test timeout behavior |
| Streaming - Start workflow | ✅ | Start streaming workflow |
| Streaming - Read during execution | ✅ | Read stream while running |
| Streaming - Read after completion | ✅ | Read complete stream |
| Streaming - Message ordering | ✅ | Verify message order |

## Use Cases Covered

### 1. Progress Tracking Dashboard
- Use Events to poll for progress percentage
- Update UI in real-time
- Show current status

### 2. Payment Webhook Integration
- Use Messaging to receive payment confirmations
- Workflow waits for external notification
- Proceed or cancel based on payment status

### 3. Live Log Viewer
- Use Streaming to show detailed logs
- Display all messages in order
- Perfect for debugging and monitoring

### 4. Multi-step Approval Workflow
- Use Messaging for human-in-the-loop
- Multiple approval gates
- Timeout handling

## Performance Notes

- **Events**: Low overhead, perfect for polling
- **Messaging**: Minimal overhead, event-driven
- **Streaming**: Higher storage for long workflows, detailed logging

## Comparison with Other Solutions

| Feature | DBOS Events | DBOS Messaging | DBOS Streaming | Redis Pub/Sub | WebSockets | Server-Sent Events |
|---------|-------------|----------------|----------------|---------------|------------|-------------------|
| Durable | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Recoverable | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Database-backed | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Workflow-integrated | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |

## Learnings & Best Practices

1. **Events are best for**:
   - Status indicators
   - Progress bars
   - Latest value queries

2. **Messaging is best for**:
   - Webhook integrations
   - Approval workflows
   - External notifications

3. **Streaming is best for**:
   - Detailed logging
   - Audit trails
   - Token-by-token LLM output

4. **Common pitfalls**:
   - Don't use streaming for simple status (use events)
   - Don't poll messaging (it's push-based)
   - Consider storage size for long-running streams

5. **Performance tips**:
   - Use appropriate timeouts for events
   - Close streams when done
   - Use topics for messaging organization

## Future Enhancements

Potential additions to this experiment:

- [ ] WebSocket wrapper for real-time streaming
- [ ] Server-Sent Events (SSE) endpoint for streaming
- [ ] Message history/replay functionality
- [ ] Stream pagination for large workflows
- [ ] Grafana dashboard integration
- [ ] React/Vue frontend example
- [ ] Load testing suite
- [ ] Multi-tenant patterns

## References

- **DBOS Documentation**: https://docs.dbos.dev/python/tutorials/workflow-communication
- **DBOS Python API**: https://docs.dbos.dev/python/reference/
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/

## Troubleshooting

### Server won't start
```bash
# Check PostgreSQL is running
psql -h localhost -U trustle -d test

# Check connection string in server.py
# Update if needed
```

### Events not found
```bash
# Increase timeout
curl "http://localhost:8000/workflow-events/wf-id/progress?timeout=10"

# Check workflow is running
# Check event key spelling
```

### Messages not received
```bash
# Verify workflow ID is correct
# Check topic name matches
# Ensure workflow hasn't timed out
```

### Stream is empty
```bash
# Wait for workflow to start
# Check STREAM_KEY matches
# Verify workflow completed successfully
```

## Contributing

To extend this experiment:

1. Add new workflow patterns in `server.py`
2. Add tests in `test_communication.py`
3. Update documentation in README files
4. Test thoroughly with various scenarios

## License

Part of the dbos_experiments repository.

---

**Created**: January 2026  
**Purpose**: Demonstrate DBOS workflow communication mechanisms  
**Status**: Complete and tested ✅
