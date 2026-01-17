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

# Step 1: Start workflow
echo "📤 Step 1: Starting workflow with 5 steps..."
echo "Command: http POST ${BASE_URL}/start-workflow-streaming/${WF_ID}/5"
echo "✅ This POST request does NOT block - returns immediately"
echo ""
http --body POST "${BASE_URL}/start-workflow-streaming/${WF_ID}/5"
echo ""

echo "⏳ Workflow is now running and writing to stream..."
echo ""

sleep 2

# Step 2: Read partial stream
echo "📖 Step 2: Reading stream (partial - workflow still running)..."
echo "Command: http GET ${BASE_URL}/workflow-stream/${WF_ID}"
echo "✅ This GET request does NOT block - returns immediately with current stream content"
echo ""
http --body GET "${BASE_URL}/workflow-stream/${WF_ID}"
echo ""

echo "💡 Notice: Stream contains messages written so far (workflow still running)"
echo ""

sleep 3

# Step 3: Read more updates
echo "📖 Step 3: Reading stream again (workflow may have written more)..."
echo ""
http --body GET "${BASE_URL}/workflow-stream/${WF_ID}"
echo ""

sleep 3

# Step 4: Read complete stream
echo "📖 Step 4: Reading complete stream (workflow should be finished)..."
echo "Command: http GET ${BASE_URL}/workflow-stream/${WF_ID}"
echo ""
http --body GET "${BASE_URL}/workflow-stream/${WF_ID}"
echo ""

echo "💡 Notice: Stream contains ALL messages written during workflow execution"
echo "   Each message has a timestamp and structured data"
echo ""

# Step 5: Demonstrate long-running workflow streaming
echo "==================================="
echo "Demonstrating Real-time Streaming"
echo "==================================="
echo ""

WF_ID_LONG="test-stream-long-$(date +%s)"

echo "📤 Step 5: Starting long-running workflow (10 steps)..."
http --body POST "${BASE_URL}/start-workflow-streaming/${WF_ID_LONG}/10"
echo ""

echo "⏳ Reading stream in real-time every 2 seconds..."
echo ""

for i in {1..6}; do
    echo "--- Read #${i} (at ${i}x2 seconds) ---"
    http --body GET "${BASE_URL}/workflow-stream/${WF_ID_LONG}" 2>&1 | grep -E '"total_messages"|"step"|"message"' | head -5
    echo ""
    sleep 2
done

echo "📖 Final read - complete stream:"
http --body GET "${BASE_URL}/workflow-stream/${WF_ID_LONG}"
echo ""

echo "==================================="
echo "✅ STREAMING TEST COMPLETED"
echo "==================================="
echo ""
echo "Summary:"
echo "  • Started workflow: ${WF_ID} (5 steps)"
echo "  • Read stream multiple times during execution"
echo "  • Started workflow: ${WF_ID_LONG} (10 steps)"
echo "  • Monitored stream in real-time"
echo ""
echo "Key Points:"
echo "  • GET /workflow-stream does NOT block - returns immediately"
echo "  • Stream stores ALL messages in order (full history)"
echo "  • Can read stream multiple times while workflow running"
echo "  • Messages persist after workflow completes"
echo "  • Perfect for: logs, LLM token streaming, progress monitoring, audit trails"
echo ""
echo "Message Structure:"
echo "  • Each message has timestamp"
echo "  • Messages are ordered (step 1, 2, 3...)"
echo "  • Different message types (start, progress, result)"
echo "  • Stream grows as workflow executes"
echo ""
