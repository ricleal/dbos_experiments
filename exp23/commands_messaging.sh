#!/bin/bash
# Test DBOS Workflow Messaging Communication
# Make this file executable: chmod +x commands_messaging.sh

echo "==================================="
echo "DBOS WORKFLOW MESSAGING TEST"
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
WF_ID="test-msg-$(date +%s)"

echo "==================================="
echo "Testing Workflow Messaging Mechanism"
echo "==================================="
echo "Workflow ID: ${WF_ID}"
echo "Description: Messaging allows clients to send notifications that workflows wait for"
echo ""

# Step 1: Start workflow (non-blocking)
echo "📤 Step 1: Starting workflow that waits for approval..."
echo "Command: http POST ${BASE_URL}/start-workflow-messaging/${WF_ID}/3"
echo "✅ This POST request does NOT block - returns immediately"
echo ""
http --body POST "${BASE_URL}/start-workflow-messaging/${WF_ID}/3"
echo ""

echo "⏳ Workflow is now running and BLOCKED at recv_async() waiting for approval..."
echo ""

sleep 2

# Step 2: Send approval (non-blocking)
echo "✉️  Step 2: Sending approval message to workflow..."
echo "Command: http POST ${BASE_URL}/send-message/${WF_ID} approved:=true message='Approved by test script'"
echo "✅ This POST request does NOT block - returns immediately after queuing message"
echo ""
http --body POST "${BASE_URL}/send-message/${WF_ID}" \
  approved:=true \
  message="Approved by test script"
echo ""

echo "📬 Message delivered! Workflow will now continue execution..."
echo ""

sleep 3

# Step 3: Demonstrate rejection
WF_ID_REJECT="test-msg-reject-$(date +%s)"

echo "==================================="
echo "Testing Rejection Flow"
echo "==================================="
echo "Workflow ID: ${WF_ID_REJECT}"
echo ""

echo "📤 Step 3: Starting another workflow..."
http --body POST "${BASE_URL}/start-workflow-messaging/${WF_ID_REJECT}/3"
echo ""

sleep 2

echo "❌ Step 4: Sending rejection message..."
echo "Command: http POST ${BASE_URL}/send-message/${WF_ID_REJECT} approved:=false reason='Rejected by test'"
echo ""
http --body POST "${BASE_URL}/send-message/${WF_ID_REJECT}" \
  approved:=false \
  reason="Rejected by test"
echo ""

sleep 2

# Step 5: Demonstrate timeout (optional)
echo "==================================="
echo "Demonstrating Timeout Behavior"
echo "==================================="
echo ""
WF_ID_TIMEOUT="test-msg-timeout-$(date +%s)"

echo "⏱️  Step 5: Starting workflow with timeout (will wait 60s)..."
echo "This workflow will timeout if no message is sent within 60 seconds"
echo ""
http --body POST "${BASE_URL}/start-workflow-messaging/${WF_ID_TIMEOUT}/3"
echo ""

echo "⏳ Workflow is waiting... (not sending any message to demonstrate timeout)"
echo "   Check server logs to see timeout behavior after 60 seconds"
echo "   Or send approval manually: http POST ${BASE_URL}/send-message/${WF_ID_TIMEOUT} approved:=true"
echo ""

echo "==================================="
echo "✅ MESSAGING TEST COMPLETED"
echo "==================================="
echo ""
echo "Summary:"
echo "  • Started workflow: ${WF_ID} (approved)"
echo "  • Started workflow: ${WF_ID_REJECT} (rejected)"
echo "  • Started workflow: ${WF_ID_TIMEOUT} (waiting for timeout)"
echo ""
echo "Key Points:"
echo "  • POST /start-workflow-messaging does NOT block"
echo "  • POST /send-message does NOT block"
echo "  • Workflow BLOCKS at recv_async() until message received"
echo "  • Messages are queued in database (reliable delivery)"
echo "  • Perfect for: approvals, webhooks, human-in-the-loop workflows"
echo ""
