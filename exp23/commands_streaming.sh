#!/bin/bash
# Test DBOS Workflow Streaming Communication
# Make this file executable: chmod +x commands_streaming.sh

echo "==================================="
echo "DBOS WORKFLOW STREAMING TEST"
echo "==================================="
echo ""

BASE_URL="http://localhost:8000"

# Check if httpie is installed
if ! command -v http &> /dev/null; then
    echo "❌ httpie is not installed!"
    echo "Install it with: pip install httpie"
    exit 1
fi

# Check if server is running
echo "Checking if server is running..."
if ! http --check-status --timeout=2 GET "${BASE_URL}/health" &> /dev/null; then
    echo "❌ Server is not running!"
    echo "Start it with: python server.py"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Generate unique workflow ID
WF_ID="test-stream-$(date +%s)"

echo "==================================="
echo "Testing Workflow Streaming Mechanism"
echo "==================================="
echo "Workflow ID: ${WF_ID}"
echo "Description: Streaming allows workflows to write real-time updates that clients can read"
echo ""

# Step 1: Start workflow with more steps for better streaming demonstration
echo "📤 Step 1: Starting workflow with 10 steps..."
echo "Command: http POST ${BASE_URL}/start-workflow-streaming/${WF_ID}/10"
echo "✅ This POST request does NOT block - returns immediately"
echo ""
http --body POST "${BASE_URL}/start-workflow-streaming/${WF_ID}/10"
echo ""

echo "⏳ Workflow is now running and writing to stream..."
echo "🔄 Polling stream to see new messages appear in real-time..."
echo ""

# Step 2-5: Poll the stream multiple times to show streaming behavior
LAST_MESSAGE_COUNT=0
for i in {1..3}; do
    echo "--- Poll #${i} (at $(date +%H:%M:%S)) ---"
    
    # Get current message count
    http --body GET "${BASE_URL}/workflow-stream/${WF_ID}"
    
    sleep 1
done

echo ""
echo "📖 Final stream snapshot - showing all messages:"
http --body GET "${BASE_URL}/workflow-stream/${WF_ID}"
echo ""

echo "💡 Key Observations:"
echo "   • Stream returns current messages IMMEDIATELY (non-blocking)"
echo "   • New messages appear as workflow executes"
echo "   • All messages persist in order (full history)"
echo "   • Stream is closed after workflow completes"
echo ""

echo "==================================="
echo "✅ STREAMING TEST COMPLETED"
echo "==================================="
echo ""
echo "Summary:"
echo "  • Started workflow: ${WF_ID} (10 steps)"
echo "  • Polled stream multiple times during execution"
echo "  • Observed new messages appearing in real-time"
echo ""
echo "Key Points About DBOS Streams:"
echo "  • read_stream() is a GENERATOR that yields values"
echo "  • Returns all messages immediately (non-blocking)"
echo "  • Stream stores complete history in order"
echo "  • Messages persist after workflow completes"
echo "  • Stream closes when workflow calls close_stream()"
echo ""
echo "Perfect Use Cases:"
echo "  • LLM token streaming (real-time AI responses)"
echo "  • Progress monitoring (build/deploy status)"
echo "  • Audit trails (action logging)"
echo "  • Live logs (server/process output)"
echo ""
echo "Streaming vs Events vs Messaging:"
echo "  • Streams: Full history, ordered messages (logs, monitoring)"
echo "  • Events: Latest value only (progress %, status)"
echo "  • Messaging: One-time delivery (approvals, notifications)"
echo ""
