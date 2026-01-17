"""
Simple client examples for interacting with DBOS workflow communication mechanisms.
This shows how to use the three communication patterns from a client application.
"""

import time
from typing import Any, Dict, List, Optional

import requests


class WorkflowClient:
    """Client for interacting with DBOS workflows"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    # ============================================================================
    # EVENTS CLIENT
    # ============================================================================

    def start_workflow_with_events(self, workflow_id: str, n_steps: int) -> Dict[str, Any]:
        """Start a workflow that publishes events"""
        response = requests.post(f"{self.base_url}/start-workflow-events/{workflow_id}/{n_steps}")
        return response.json()

    def get_workflow_event(self, workflow_id: str, event_key: str, timeout: int = 5) -> Optional[Any]:
        """Get a specific event from a workflow"""
        try:
            response = requests.get(
                f"{self.base_url}/workflow-events/{workflow_id}/{event_key}",
                params={"timeout": timeout},
            )
            if response.status_code == 200:
                return response.json()["value"]
            return None
        except Exception:
            return None

    def get_all_workflow_events(self, workflow_id: str) -> Dict[str, Any]:
        """Get all events from a workflow"""
        response = requests.get(f"{self.base_url}/workflow-events/{workflow_id}/all")
        return response.json()["events"]

    def poll_until_complete(self, workflow_id: str, poll_interval: float = 1.0) -> Dict[str, Any]:
        """Poll workflow progress until completion"""
        print(f"Polling workflow {workflow_id}...")

        while True:
            progress = self.get_workflow_event(workflow_id, "progress", timeout=2)
            status = self.get_workflow_event(workflow_id, "status", timeout=2)

            if progress is not None:
                print(f"  Progress: {progress}% - Status: {status}")

                if progress == 100:
                    result = self.get_workflow_event(workflow_id, "result", timeout=5)
                    if result is not None:
                        return result
                    # If result is None, return empty dict
                    return {}

            time.sleep(poll_interval)

    # ============================================================================
    # MESSAGING CLIENT
    # ============================================================================

    def start_workflow_with_messaging(self, workflow_id: str, n_steps: int) -> Dict[str, Any]:
        """Start a workflow that waits for messages"""
        response = requests.post(f"{self.base_url}/start-workflow-messaging/{workflow_id}/{n_steps}")
        return response.json()

    def send_approval(self, workflow_id: str, approved: bool, message: str = "") -> Dict[str, Any]:
        """Send approval/rejection to a workflow"""
        payload = {"approved": approved, "message": message, "timestamp": time.time()}
        response = requests.post(f"{self.base_url}/send-message/{workflow_id}", json=payload)
        return response.json()

    def send_custom_message(self, workflow_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a custom message to a workflow"""
        response = requests.post(f"{self.base_url}/send-message/{workflow_id}", json=message)
        return response.json()

    # ============================================================================
    # STREAMING CLIENT
    # ============================================================================

    def start_workflow_with_streaming(self, workflow_id: str, n_steps: int) -> Dict[str, Any]:
        """Start a workflow that streams updates"""
        response = requests.post(f"{self.base_url}/start-workflow-streaming/{workflow_id}/{n_steps}")
        return response.json()

    def read_stream(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Read all values from a workflow stream"""
        response = requests.get(f"{self.base_url}/workflow-stream/{workflow_id}")
        return response.json()["stream_values"]

    def stream_live_updates(self, workflow_id: str, poll_interval: float = 1.0, max_polls: int = 30):
        """Stream live updates from a workflow (polling-based)"""
        print(f"Streaming updates from workflow {workflow_id}...")
        last_count = 0

        for _ in range(max_polls):
            try:
                stream_values = self.read_stream(workflow_id)

                # Show only new messages
                if len(stream_values) > last_count:
                    for msg in stream_values[last_count:]:
                        msg_type = msg.get("type", "unknown")
                        msg_text = msg.get("message", str(msg))
                        print(f"  [{msg_type}] {msg_text}")

                    last_count = len(stream_values)

                    # Check if workflow completed
                    if any(m.get("type") == "complete" for m in stream_values):
                        print("Workflow completed!")
                        break

                time.sleep(poll_interval)
            except Exception:
                time.sleep(poll_interval)
                continue


# ============================================================================
# USAGE EXAMPLES
# ============================================================================


def example_events_usage():
    """Example: Using workflow events for progress tracking"""
    print("\n=== EXAMPLE 1: Workflow Events ===\n")

    client = WorkflowClient()
    workflow_id = f"client-events-{int(time.time())}"

    # Start workflow
    print(f"Starting workflow: {workflow_id}")
    result = client.start_workflow_with_events(workflow_id, n_steps=3)
    print(f"Started: {result['message']}")

    # Poll until complete
    final_result = client.poll_until_complete(workflow_id)
    print(f"\nFinal result: {final_result}")

    # Get all events
    all_events = client.get_all_workflow_events(workflow_id)
    print(f"All events: {all_events}")


def example_messaging_usage():
    """Example: Using workflow messaging for approval flow"""
    print("\n=== EXAMPLE 2: Workflow Messaging ===\n")

    client = WorkflowClient()
    workflow_id = f"client-msg-{int(time.time())}"

    # Start workflow
    print(f"Starting workflow: {workflow_id}")
    result = client.start_workflow_with_messaging(workflow_id, n_steps=3)
    print(f"Started: {result['message']}")

    # Simulate waiting for human approval
    print("\nSimulating approval process...")
    time.sleep(2)

    # Send approval
    print("Sending approval...")
    approval = client.send_approval(workflow_id, approved=True, message="Approved by client")
    print(f"Approval sent: {approval}")

    print("\nWorkflow will now proceed with processing.")


def example_streaming_usage():
    """Example: Using workflow streaming for live updates"""
    print("\n=== EXAMPLE 3: Workflow Streaming ===\n")

    client = WorkflowClient()
    workflow_id = f"client-stream-{int(time.time())}"

    # Start workflow
    print(f"Starting workflow: {workflow_id}")
    result = client.start_workflow_with_streaming(workflow_id, n_steps=5)
    print(f"Started: {result['message']}")

    print("\nStreaming live updates:")
    # Stream live updates
    client.stream_live_updates(workflow_id, poll_interval=1.0, max_polls=30)


def example_combined_usage():
    """Example: Using multiple mechanisms together"""
    print("\n=== EXAMPLE 4: Combined Usage ===\n")

    client = WorkflowClient()

    # Use events for one workflow
    wf1 = f"combined-events-{int(time.time())}"
    print(f"1. Starting workflow with events: {wf1}")
    client.start_workflow_with_events(wf1, n_steps=2)

    # Use messaging for another
    wf2 = f"combined-msg-{int(time.time())}"
    print(f"2. Starting workflow with messaging: {wf2}")
    client.start_workflow_with_messaging(wf2, n_steps=2)

    # Use streaming for a third
    wf3 = f"combined-stream-{int(time.time())}"
    print(f"3. Starting workflow with streaming: {wf3}")
    client.start_workflow_with_streaming(wf3, n_steps=3)

    # Approve the messaging workflow
    time.sleep(2)
    print(f"\n4. Approving workflow {wf2}")
    client.send_approval(wf2, approved=True)

    # Check progress on events workflow
    print(f"\n5. Checking progress on {wf1}")
    for _ in range(5):
        progress = client.get_workflow_event(wf1, "progress", timeout=2)
        if progress is not None:
            print(f"   Progress: {progress}%")
            if progress == 100:
                break
        time.sleep(1)

    # Read stream from streaming workflow
    print(f"\n6. Reading stream from {wf3}")
    time.sleep(5)
    stream_values = client.read_stream(wf3)
    print(f"   Received {len(stream_values)} stream messages")


if __name__ == "__main__":
    print("=" * 70)
    print("DBOS Workflow Communication - Client Examples")
    print("=" * 70)
    print("\nMake sure the server is running: python server.py")
    print("=" * 70)

    # Check server
    try:
        response = requests.get("http://localhost:8000/health")
        print("\n✓ Server is running\n")
    except Exception:
        print("\n✗ ERROR: Server not running!")
        print("  Please start the server first: python server.py\n")
        exit(1)

    # Run examples
    try:
        example_events_usage()
        time.sleep(2)

        example_messaging_usage()
        time.sleep(2)

        example_streaming_usage()
        time.sleep(2)

        # Uncomment to run combined example
        # example_combined_usage()

        print("\n" + "=" * 70)
        print("All client examples completed successfully! 🎉")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
