# Visual Guide: DBOS Workflow Communication Mechanisms

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   EVENTS     │  │  MESSAGING   │  │  STREAMING   │          │
│  │   Client     │  │   Client     │  │   Client     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ GET              │ POST             │ GET
          │ (query)          │ (send)           │ (read)
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼──────────────────┐
│         ▼                  ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   /workflow- │  │     /send-   │  │   /workflow- │          │
│  │   events/    │  │    message/  │  │    stream/   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│                     FASTAPI SERVER                               │
├──────────────────────────────────────────────────────────────────┤
│                         DBOS RUNTIME                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   WORKFLOW EXECUTION                      │   │
│  │                                                            │   │
│  │  set_event()  ◄───┐         ┌───► recv()                │   │
│  │  get_event()      │         │     send()                 │   │
│  │                   │         │                             │   │
│  │              ┌────┴─────────┴────┐                       │   │
│  │              │  System Database  │                       │   │
│  │              │  (Events, Msgs,   │  write_stream()       │   │
│  │              │   Streams)        │  read_stream()        │   │
│  │              └───────────────────┘  close_stream()       │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Mechanism 1: EVENTS

**Direction:** Workflow → Client (Pull)

```
Client                    Server                  Workflow
  │                         │                         │
  │  POST /start-wf-events  │                         │
  ├────────────────────────►│  start_workflow()       │
  │                         ├────────────────────────►│
  │                         │                         │
  │                         │         set_event("progress", 25)
  │                         │                         │
  │  GET /events/progress   │                         │
  ├────────────────────────►│  get_event()            │
  │◄────────────────────────┤                         │
  │    {"value": 25}        │                         │
  │                         │                         │
  │                         │         set_event("progress", 50)
  │  GET /events/progress   │                         │
  ├────────────────────────►│  get_event()            │
  │◄────────────────────────┤                         │
  │    {"value": 50}        │                         │
  │                         │                         │
  │                         │         set_event("progress", 100)
  │  GET /events/all        │                         │
  ├────────────────────────►│  get_all_events()       │
  │◄────────────────────────┤                         │
  │    {progress:100,...}   │                         │
```

**Key Characteristics:**
- Client polls for updates
- Only latest value is stored per key
- Perfect for status/progress indicators
- Low database overhead

**⚠️ Blocking Behavior:**
- `GET /workflow-events/{id}/{key}`: **BLOCKS** until event available or timeout (default 60s)
- `GET /workflow-events/{id}/all`: **DOES NOT BLOCK** - returns immediately with all current events
- Workflow `set_event()`: **DOES NOT BLOCK** - publishes immediately
- Server `get_event()`: **BLOCKS** waiting for event with timeout

## Mechanism 2: MESSAGING

**Direction:** Client → Workflow (Push)

```
Client                    Server                  Workflow
  │                         │                         │
  │ POST /start-wf-msg      │                         │
  ├────────────────────────►│  start_workflow()       │
  │  [returns immediately]  │                         │
  │◄────────────────────────┤                         │
  │                         │                         │
  │                         │         await recv_async() [BLOCKED]
  │                         │         ▲               │
  │                         │         │ Workflow waiting
  │                         │         │               │
  │ POST /send-message      │         │               │
  │  {approved: true}       │         │               │
  ├────────────────────────►│  send()│               │
  │  [returns immediately]  │         │               │
  │◄────────────────────────┤         │               │
  │                         │         │               │
  │                         │         │  Message delivered!
  │                         │         ▼               │
  │                         │         recv_async() returns!
  │                         │                         │
  │                         │         continue execution...
  │                         │                         │
```

**Key Characteristics:**
- Client pushes notifications to workflow (non-blocking)
- Workflow **BLOCKS** at `await recv_async()` until message received
- Perfect for approvals and webhooks
- Supports topics for message routing

**⚠️ Blocking Behavior:**
- `/send-message` endpoint: **DOES NOT BLOCK** - returns immediately
- Workflow `await recv_async()`: **BLOCKS** until message arrives or timeout
- ❌ Never use `recv()` in async workflows - use `await recv_async()`!

## Mechanism 3: STREAMING

**Direction:** Workflow → Client (Pull with History)

```
Client                    Server                  Workflow
  │                         │                         │
  │ POST /start-wf-stream   │                         │
  ├────────────────────────►│  start_workflow()       │
  │                         ├────────────────────────►│
  │                         │                         │
  │                         │         write_stream("msg 1")
  │                         │         write_stream("msg 2")
  │                         │                         │
  │  GET /stream/wf-id      │                         │
  ├────────────────────────►│  read_stream()          │
  │◄────────────────────────┤                         │
  │  [msg1, msg2]           │                         │
  │                         │                         │
  │                         │         write_stream("msg 3")
  │                         │         write_stream("msg 4")
  │                         │                         │
  │  GET /stream/wf-id      │                         │
  ├────────────────────────►│  read_stream()          │
  │◄────────────────────────┤                         │
  │  [msg1, msg2, msg3, msg4]                         │
  │                         │                         │
  │                         │         close_stream()
```

**Key Characteristics:**
- Client polls for updates
- All values are stored in order
- Perfect for logs and detailed progress
- Can grow large for long-running workflows

**⚠️ Blocking Behavior:**
- `GET /workflow-stream/{id}`: **DOES NOT BLOCK** - returns immediately with all current stream values
- Workflow `write_stream()`: **DOES NOT BLOCK** - writes immediately
- Workflow `close_stream()`: **DOES NOT BLOCK** - closes immediately
- Server `read_stream()`: **DOES NOT BLOCK** - returns generator immediately

## Comparison Matrix

```
┌──────────────────┬─────────────┬─────────────┬─────────────┐
│                  │   EVENTS    │  MESSAGING  │  STREAMING  │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Direction        │ WF → Client │ Client → WF │ WF → Client │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Client Action    │ Pull (poll) │ Push (send) │ Pull (poll) │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Data Persistence │ Latest Only │ Queued      │ Full History│
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Client Blocks?   │ Yes (GET)   │ No (POST)   │ No (GET)    │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Endpoint Blocks? │ Yes (get_ev)│ No (send)   │ No (read)   │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Workflow Blocks? │ No          │ Yes (recv)  │ No          │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Storage Size     │ Small       │ Small       │ Can be Large│
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Best For         │ Status      │ Approvals   │ Logs        │
└──────────────────┴─────────────┴─────────────┴─────────────┘
```

## Use Case Examples

### Example 1: Progress Bar
**Use: EVENTS**
```python
# Workflow
for i in range(100):
    DBOS.set_event("progress", i)
    process_item(i)

# Client (polling)
while True:
    progress = get_event(wf_id, "progress")
    update_progress_bar(progress)
    if progress == 100: break
```

### Example 2: Payment Gateway
**Use: MESSAGING**
```python
# Workflow
create_checkout_session()
payment = DBOS.recv(topic="payment", timeout=3600)
if payment["status"] == "paid":
    fulfill_order()

# Payment webhook
@app.post("/webhook")
def payment_webhook(wf_id, status):
    DBOS.send(wf_id, {"status": status}, topic="payment")
```

### Example 3: LLM Streaming
**Use: STREAMING**
```python
# Workflow
for token in llm.generate():
    DBOS.write_stream("tokens", token)
DBOS.close_stream("tokens")

# Client
for token in DBOS.read_stream(wf_id, "tokens"):
    display_token(token)
```

## Performance Characteristics

### Events
```
Database Writes:  ████░░░░░░ (Low - Only updates)
Database Reads:   ████░░░░░░ (Low - Single row)
Client Polling:   ████████░░ (Medium-High)
Best For:         Real-time dashboards
```

### Messaging
```
Database Writes:  ████░░░░░░ (Low - Single message)
Database Reads:   ████░░░░░░ (Low - Dequeue once)
Client Polling:   ░░░░░░░░░░ (None - push based)
Best For:         Webhooks, rare notifications
```

### Streaming
```
Database Writes:  ████████░░ (Medium-High - Append-only)
Database Reads:   ████████░░ (Medium-High - Full scan)
Client Polling:   ████████░░ (Medium-High)
Best For:         Detailed logging, audit trails
```

## Decision Tree

```
Start: What do you need?
│
├─► Need to send data TO workflow?
│   └─► Use MESSAGING (send/recv)
│
├─► Need workflow to send data to client?
│   │
│   ├─► Need complete history?
│   │   └─► Use STREAMING (write_stream/read_stream)
│   │
│   └─► Only need latest value?
│       └─► Use EVENTS (set_event/get_event)
```

## Real-World Scenarios

### Scenario 1: File Processing Pipeline
```
Events:     Track overall progress (45% complete)
Streaming:  Log each file processed with details
Messaging:  Receive "pause" command from admin
```

### Scenario 2: E-commerce Checkout
```
Events:     Current step (cart → payment → confirmation)
Messaging:  Payment processor webhook notification
Streaming:  Not needed (simple workflow)
```

### Scenario 3: AI Agent Task
```
Events:     Current task stage
Streaming:  Full reasoning trace / chain-of-thought
Messaging:  Human feedback on intermediate results
```

### Scenario 4: Data ETL Job
```
Events:     Records processed (12,450 / 50,000)
Streaming:  Error logs and warnings
Messaging:  Cancel signal from monitoring system
```

## Summary

- **Choose EVENTS** when you need the latest status/progress
- **Choose MESSAGING** when external systems need to notify workflows
- **Choose STREAMING** when you need complete history or real-time logs

All three mechanisms are:
- ✅ Durable (persisted in database)
- ✅ Recoverable (survive restarts)
- ✅ Reliable (guaranteed delivery)
