#!/bin/bash
# Test DBOS Workflow Events Communication
# Make this file executable: chmod +x commands_events.sh

echo "==================================="
echo "DBOS WORKFLOW EVENTS TEST"
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
WF_ID="test-events-$(date +%s)"

echo "==================================="
echo "Testing Workflow Events Mechanism"
echo "==================================="
echo "Workflow ID: ${WF_ID}"
echo "Description: Events allow workflows to publish key-value pairs that clients can query"
echo ""

# Step 1: Start workflow
echo "📤 Step 1: Starting workflow with 3 steps..."
echo "Command: http POST ${BASE_URL}/start-workflow-events/${WF_ID}/3"
echo ""
http --body POST "${BASE_URL}/start-workflow-events/${WF_ID}/3"
echo ""

# sleep 1

# Show all events before Step 2
echo "📋 Current events state:"
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/all"
echo ""

# Step 2: Query progress
echo "📊 Step 2: Querying progress event..."
echo "Command: http GET ${BASE_URL}/workflow-events/${WF_ID}/progress"
echo "⚠️  This request BLOCKS until event is available or timeout (60s)"
echo ""
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/progress"
echo ""

# sleep 1

# Show all events before Step 3
echo "📋 Current events state:"
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/all"
echo ""

# Step 3: Query status
echo "📝 Step 3: Querying status event..."
echo "Command: http GET ${BASE_URL}/workflow-events/${WF_ID}/status"
echo ""
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/status"
echo ""

# sleep 2

# Show all events before Step 4
echo "📋 Current events state:"
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/all"
echo ""

# Step 4: Query result (will wait for workflow to complete)
echo "🎯 Step 4: Querying result event (waiting for completion)..."
echo "Command: http GET ${BASE_URL}/workflow-events/${WF_ID}/result"
echo "⚠️  This will BLOCK until workflow completes and publishes result"
echo ""
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/result"
echo ""

# Show all events before Step 5
echo "📋 Current events state:"
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/all"
echo ""

# Step 5: Get all events
echo "📋 Step 5: Getting all events at once (final state)..."
echo "Command: http GET ${BASE_URL}/workflow-events/${WF_ID}/all"
echo "✅ This does NOT block - returns immediately with all current events"
echo ""
http --body GET "${BASE_URL}/workflow-events/${WF_ID}/all"
echo ""

echo "==================================="
echo "✅ EVENTS TEST COMPLETED"
echo "==================================="
echo ""
echo "Summary:"
echo "  • Started workflow: ${WF_ID}"
echo "  • Queried progress, status, and result events"
echo "  • Retrieved all events at once"
echo ""
echo "Key Points:"
echo "  • Events store only the LATEST value per key"
echo "  • GET requests BLOCK until event available or timeout"
echo "  • Perfect for: progress tracking, status indicators, final results"
echo ""
