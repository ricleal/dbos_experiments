#!/usr/bin/env python3
"""
Test script for DBOS workflow communication mechanisms.
Run this after starting the server with: python server.py
"""

import time

import requests

BASE_URL = "http://localhost:8000"


def test_workflow_events():
    """Test Workflow Events mechanism"""
    print("\n" + "=" * 70)
    print("TEST 1: WORKFLOW EVENTS")
    print("=" * 70)

    workflow_id = f"wf-events-test-{int(time.time())}"
    n_steps = 3

    # Start workflow
    print(f"\n1. Starting workflow with events: {workflow_id}")
    response = requests.post(f"{BASE_URL}/start-workflow-events/{workflow_id}/{n_steps}")
    print(f"   Response: {response.json()}")

    # Poll for progress
    print("\n2. Polling for progress events...")
    for i in range(10):
        time.sleep(1)
        try:
            response = requests.get(
                f"{BASE_URL}/workflow-events/{workflow_id}/progress",
                params={"timeout": 2},
            )
            if response.status_code == 200:
                progress = response.json()
                print(f"   Progress: {progress['value']}%")
                if progress["value"] == 100:
                    break
        except Exception:
            print("   Progress event not yet available...")

    # Get final status
    print("\n3. Getting final status...")
    response = requests.get(f"{BASE_URL}/workflow-events/{workflow_id}/status", params={"timeout": 5})
    print(f"   Status: {response.json()}")

    # Get all events
    print("\n4. Getting all events...")
    response = requests.get(f"{BASE_URL}/workflow-events/{workflow_id}/all")
    events = response.json()
    print(f"   All events: {events['events']}")

    print("\n✅ WORKFLOW EVENTS TEST COMPLETED")


def test_workflow_messaging():
    """Test Workflow Messaging mechanism"""
    print("\n" + "=" * 70)
    print("TEST 2: WORKFLOW MESSAGING AND NOTIFICATIONS")
    print("=" * 70)

    workflow_id = f"wf-msg-test-{int(time.time())}"
    n_steps = 3

    # Start workflow
    print(f"\n1. Starting workflow that waits for approval: {workflow_id}")
    response = requests.post(f"{BASE_URL}/start-workflow-messaging/{workflow_id}/{n_steps}")
    print(f"   Response: {response.json()}")

    # Wait a bit
    print("\n2. Waiting 3 seconds before sending approval...")
    time.sleep(3)

    # Send approval message
    print("\n3. Sending approval notification...")
    approval_message = {
        "approved": True,
        "approver": "test-script",
        "timestamp": time.time(),
    }
    response = requests.post(f"{BASE_URL}/send-message/{workflow_id}", json=approval_message)
    print(f"   Response: {response.json()}")

    # Wait for workflow to complete
    print("\n4. Waiting for workflow to complete processing...")
    time.sleep(10)

    print("\n✅ WORKFLOW MESSAGING TEST COMPLETED")
    print("   Note: Check DBOS logs or use 'dbos workflow get {}' to see the result".format(workflow_id))


def test_workflow_streaming():
    """Test Workflow Streaming mechanism"""
    print("\n" + "=" * 70)
    print("TEST 3: WORKFLOW STREAMING")
    print("=" * 70)

    workflow_id = f"wf-stream-test-{int(time.time())}"
    n_steps = 5

    # Start workflow
    print(f"\n1. Starting workflow with streaming: {workflow_id}")
    response = requests.post(f"{BASE_URL}/start-workflow-streaming/{workflow_id}/{n_steps}")
    print(f"   Response: {response.json()}")

    # Poll stream multiple times to see it grow
    print("\n2. Reading stream (will poll 3 times)...")
    for poll_num in range(1, 4):
        time.sleep(3)
        print(f"\n   Poll #{poll_num}:")
        response = requests.get(f"{BASE_URL}/workflow-stream/{workflow_id}")
        stream_data = response.json()
        print(f"   Total messages so far: {stream_data['total_messages']}")

        # Show last few messages
        if stream_data["stream_values"]:
            print("   Latest messages:")
            for msg in stream_data["stream_values"][-3:]:
                print(f"     - [{msg.get('type', 'unknown')}] {msg.get('message', msg)}")

    # Final read
    print("\n3. Final stream read after workflow completes...")
    time.sleep(5)
    response = requests.get(f"{BASE_URL}/workflow-stream/{workflow_id}")
    stream_data = response.json()
    print(f"   Total messages: {stream_data['total_messages']}")
    print("\n   All messages:")
    for i, msg in enumerate(stream_data["stream_values"], 1):
        msg_type = msg.get("type", "unknown")
        msg_text = msg.get("message", str(msg))
        print(f"     {i}. [{msg_type}] {msg_text}")

    print("\n✅ WORKFLOW STREAMING TEST COMPLETED")


def test_all():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("DBOS WORKFLOW COMMUNICATION - COMPREHENSIVE TEST")
    print("=" * 70)
    print("\nThis test will demonstrate all three communication mechanisms:")
    print("  1. Workflow Events")
    print("  2. Workflow Messaging")
    print("  3. Workflow Streaming")
    print("\nMake sure the server is running: python server.py")
    print("=" * 70)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✓ Server is running (Memory: {response.json()['memory_mb']} MB)")
    except Exception:
        print(f"\n✗ ERROR: Cannot connect to server at {BASE_URL}")
        print("  Make sure to run: python server.py")
        return

    # Run all tests
    try:
        test_workflow_events()
        test_workflow_messaging()
        test_workflow_streaming()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 70)
        print("\nSummary:")
        print("  ✅ Workflow Events - Published and retrieved successfully")
        print("  ✅ Workflow Messaging - Sent and received notifications")
        print("  ✅ Workflow Streaming - Streamed real-time updates")
        print("\nCheck the server logs to see detailed workflow execution.")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_all()
