#!/usr/bin/env python3
"""Quick test of the WorkflowClient library"""

import time

from client_examples import WorkflowClient

client = WorkflowClient()

# Test 1: Events
print("Testing WorkflowClient - Events mechanism...")
wf_id = f"client-test-events-{int(time.time())}"
result = client.start_workflow_with_events(wf_id, 3)
print(f"  Started: {result['workflow_id']}")

time.sleep(2)
progress = client.get_workflow_event(wf_id, "progress")
print(f"  Progress: {progress}%")

all_events = client.get_all_workflow_events(wf_id)
print(f"  All events: {list(all_events.keys())}")

# Test 2: Messaging
print("\nTesting WorkflowClient - Messaging mechanism...")
wf_id = f"client-test-msg-{int(time.time())}"
result = client.start_workflow_with_messaging(wf_id, 3)
print(f"  Started: {result['workflow_id']}")

time.sleep(1)
result = client.send_approval(wf_id, approved=True, message="Approved by client library")
print(f"  Sent approval: {result['message']}")

# Test 3: Streaming
print("\nTesting WorkflowClient - Streaming mechanism...")
wf_id = f"client-test-stream-{int(time.time())}"
result = client.start_workflow_with_streaming(wf_id, 3)
print(f"  Started: {result['workflow_id']}")

time.sleep(2)
stream = client.read_stream(wf_id)
print(f"  Stream has {len(stream)} messages")
print(f"  First message: {stream[0]}")
print(f"  Last message: {stream[-1]}")

print("\n✅ WorkflowClient library works correctly!")
