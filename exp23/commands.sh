#!/bin/bash
# DBOS Workflow Communication - Quick Test Commands (All 3 Mechanisms)
# Make this file executable: chmod +x commands.sh

echo "==================================="
echo "DBOS Workflow Communication Tests"
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

# Test 1: Events
echo "==================================="
echo "TEST 1: WORKFLOW EVENTS"
echo "==================================="
WF_EVENT="test-events-$(date +%s)"
echo ""
echo "1. Starting workflow with events: ${WF_EVENT}"
http --body POST "${BASE_URL}/start-workflow-events/${WF_EVENT}/3"
echo ""

sleep 2

echo "2. Querying progress (BLOCKS until available)..."
http --body GET "${BASE_URL}/workflow-events/${WF_EVENT}/progress"
echo ""

echo "3. Querying status..."
http --body GET "${BASE_URL}/workflow-events/${WF_EVENT}/status"
echo ""

sleep 3

echo "4. Getting all events (does NOT block)..."
http --body GET "${BASE_URL}/workflow-events/${WF_EVENT}/all"
echo ""

# Test 2: Messaging
echo "==================================="
echo "TEST 2: WORKFLOW MESSAGING"
echo "==================================="
WF_MSG="test-msg-$(date +%s)"
echo ""
echo "1. Starting workflow that waits for approval (in background): ${WF_MSG}"
# Don't redirect output so we can see any errors
curl -X POST "${BASE_URL}/start-workflow-messaging/${WF_MSG}/3" &
CURL_PID=$!
echo "   Workflow start request sent (PID: $CURL_P: ${WF_MSG}"
echo "   (POST does NOT block - returns immediately)"
http --body POST "${BASE_URL}/start-workflow-messaging/${WF_MSG}/3"
echo ""

sleep 2

echo "2. Sending approval message (POST does NOT block)..."
echo "   Workflow is BLOCKED at recv_async() waiting for this message"
http --body POST "${BASE_URL}/send-message/${WF_MSG}" \
  approved:=true \
  message="Approved by test script"
echo ""

echo "3. Message delivered! Workflow will now continue..."
sleep 5
echo ""

# Test 3: Streaming
echo "==================================="
echo "TEST 3: WORKFLOW STREAMING"
echo "==================================="
WF_STREAM="test-stream-$(date +%s)"
echo ""
echo "1. Starting workflow with streaming: ${WF_STREAM}"
http --body POST "${BASE_URL}/start-workflow-streaming/${WF_STREAM}/5"
echo ""

sleep 2

echo "2. Reading stream (partial - GET does NOT block)..."
http --body GET "${BASE_URL}/workflow-stream/${WF_STREAM}"
echo ""

sleep 5

echo "3. Reading complete stream..."
http --body GET "${BASE_URL}/workflow-stream/${WF_STREAM}"
echo ""

echo "==================================="
echo "✅ ALL TESTS COMPLETED"
echo "==================================="
echo ""
echo "For detailed tests of individual mechanisms, run:"
echo "  • ./commands_events.sh"
echo "  • ./commands_messaging.sh"
echo "  • ./commands_streaming.sh

echo "==================================="
echo "ALL TESTS COMPLETED! ✅"
echo "==================================="
echo ""
echo "Workflow IDs used:"
echo "  Events:    ${WF_EVENT}"
echo "  Messaging: ${WF_MSG}"
echo "  Streaming: ${WF_STREAM}"
echo ""
echo "Check server logs for detailed execution info."
echo ""
