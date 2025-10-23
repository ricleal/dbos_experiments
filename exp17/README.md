# ELT Pipeline with DBOS Workflows

A resilient, distributed ELT (Extract, Load, Transform) pipeline built with DBOS workflows, featuring automatic failure recovery, memory-efficient batching, and data deduplication.

## Overview

This project demonstrates a production-ready ELT pipeline that processes users from multiple external APIs across different organizations and integrations. The pipeline uses DBOS workflows to provide automatic recovery from any failure, ensuring exactly-once semantics and progress tracking.

## Features

- **🔄 Hierarchical Workflows**: Four-level workflow orchestration for fine-grained recovery
- **💾 Memory-Efficient Batching**: Two-level batching strategy prevents OOM errors
- **🔁 Automatic Recovery**: Built-in retry logic for transient failures
- **🧹 Data Deduplication**: SQL window functions handle duplicates from retries
- **⏰ Scheduled Execution**: Daily automated runs via cron-like scheduling
- **🌐 Remote Triggering**: Client can trigger workflows on demand
- **❤️ Health Monitoring**: HTTP health check endpoint for service monitoring
- **🏢 Multi-Tenant Architecture**: Complete data isolation per organization and integration

## Project Structure

```
exp17/
├── elt.py              # Main ELT pipeline workflows
├── server.py           # DBOS server with health check
├── client.py           # Remote workflow triggering client
├── data.py             # Data models and fake data generation
├── db.py               # Database operations and SQL queries
├── ARCHITECTURE.md     # Detailed architecture documentation
└── data.db             # SQLite database (created at runtime)
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for DBOS system database)
- Poetry or pip for dependency management

### Installation

```bash
# Install dependencies
poetry install

# Or with pip
pip install dbos faker
```

### Environment Setup

Set the PostgreSQL connection string for DBOS:

```bash
export DBOS_DATABASE_URL="postgresql://postgres:dbos@localhost:5432/test?connect_timeout=10"
```

### Running the Server

Start the ELT pipeline server:

```bash
python server.py
```

This will:
- Initialize the SQLite database and seed test data
- Launch DBOS and register all workflows
- Start a health check server on port 8080
- Begin processing scheduled workflows

Health check endpoint:
```bash
curl http://localhost:8080/health
```

### Using the Client

The client allows you to trigger workflows remotely:

```bash
# Trigger the root orchestration workflow (processes all integrations)
python client.py start root_orchestration_workflow

# Trigger ELT pipeline for a specific org/integration
python client.py start elt_pipeline_workflow \
    organization_id=org-001 \
    connected_integration_id=<uuid-here>

# Trigger with custom batch parameters
python client.py start extract_and_load_workflow \
    organization_id=org-001 \
    connected_integration_id=<uuid-here> \
    num_batches=5 \
    batch_size=20

# Check workflow status
python client.py status <workflow-id>

# List all workflows
python client.py list

# List workflows with filters
python client.py list status=PENDING
python client.py list status=SUCCESS limit=10
```

## Architecture

### Workflow Hierarchy

```
Scheduled Trigger (daily at 5:20 AM GMT)
└── Root Orchestration Workflow
    └── ELT Pipeline Workflow (per org/integration)
        ├── Extract & Load Workflow
        │   └── Extract & Load Batch Workflow (per batch)
        │       ├── fetch_users_from_api (per page)
        │       └── insert_users_to_staging (per batch)
        ├── CDC Detection Workflow
        ├── Apply to Latest Workflow
        └── Sync to Postgres Workflow
```

### Batching Strategy

The pipeline uses a two-level batching approach to manage memory:

- **10 batches** × **10 pages per batch** = **100 total pages**
- **10 users per page** = **1,000 users per org/integration**
- Only one batch (100 users) in memory at a time

This prevents OOM errors while maintaining efficiency.

### Data Deduplication

Uses SQL window functions to handle duplicates created by automatic retries:

```sql
WITH ranked_users AS (
    SELECT *, 
           ROW_NUMBER() OVER (
               PARTITION BY id, workflow_id
               ORDER BY created_at DESC
           ) as rn
    FROM users
)
SELECT COUNT(*) FROM ranked_users WHERE rn = 1
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Database Schema

The pipeline uses four tables to implement a proper ELT flow:

### `connected_integrations`

Stores integration configurations for each organization:

```sql
CREATE TABLE connected_integrations (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_data TEXT NOT NULL  -- JSON: {permission_source_name, api_endpoint, ...}
)
```

### `users_staging`

Staging table for raw data extracted from APIs (supports duplicates for idempotency):

```sql
CREATE TABLE users_staging (
    id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    connected_integration_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at DATETIME DEFAULT(datetime('subsec')),
    PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, created_at)
)
```

**Multi-Tenant Primary Key:** `(id, organization_id, connected_integration_id, workflow_id, created_at)`
- First 3 fields form the multi-tenant user identity
- User IDs can be duplicated across different organizations/integrations
- `workflow_id` and `created_at` enable idempotent retries

### `users_cdc`

Change Data Capture table that tracks INSERT, UPDATE, and DELETE operations:

```sql
CREATE TABLE users_cdc (
    id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    connected_integration_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    detected_at DATETIME DEFAULT(datetime('subsec')),
    PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, detected_at)
)
```

**Multi-Tenant Primary Key:** `(id, organization_id, connected_integration_id, workflow_id, detected_at)`
- Ensures CDC records are isolated per organization/integration
- `workflow_id` and `detected_at` support idempotent detection

### `users_latest`

Latest state table containing deduplicated, current records:

```sql
CREATE TABLE users_latest (
    id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    connected_integration_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    last_updated DATETIME DEFAULT(datetime('subsec')),
    PRIMARY KEY (id, organization_id, connected_integration_id)
)
```

**Multi-Tenant Primary Key:** `(id, organization_id, connected_integration_id)`
- Enforces uniqueness per user per organization per integration
- Allows same user ID to exist in different tenant contexts

## ELT Pipeline Stages

The pipeline follows a proper ELT flow with four distinct stages:

### Stage 1: Extract & Load
- Fetches data from external APIs in batches
- Loads raw data into `users_staging` table
- Handles duplicates from retries using composite primary key
- Uses window functions for deduplication

### Stage 2: CDC Detection
- Compares deduplicated staging data with `users_latest`
- Identifies INSERT operations (new records)
- Identifies UPDATE operations (changed records)
- Populates `users_cdc` table with detected changes

**SQL Logic (Multi-Tenant Aware):**
```sql
-- INSERTs: Records in staging but not in latest
SELECT * FROM staging_deduped
LEFT JOIN users_latest 
    ON staging.id = latest.id 
    AND staging.organization_id = latest.organization_id
    AND staging.connected_integration_id = latest.connected_integration_id
WHERE latest.id IS NULL

-- UPDATEs: Records in both with different data
SELECT * FROM staging_deduped
INNER JOIN users_latest 
    ON staging.id = latest.id
    AND staging.organization_id = latest.organization_id
    AND staging.connected_integration_id = latest.connected_integration_id
WHERE staging.name != latest.name OR staging.email != latest.email
```

All JOINs include `organization_id` and `connected_integration_id` to ensure proper multi-tenant isolation.

### Stage 3: Apply to Latest
- Reads changes from `users_cdc` table
- Applies INSERT and UPDATE operations to `users_latest`
- Uses `INSERT OR REPLACE` for atomic updates
- Maintains current state in the latest table

### Stage 4: Sync to Postgres
- Reads changes from `users_cdc` table
- Simulates syncing to a Postgres main database
- In production, would execute actual INSERT/UPDATE/DELETE on Postgres
- Tracks sync status and timestamps

## Failure Simulation

The pipeline includes intentional failures for testing resilience:

| Failure Type | Location | Probability | Retry Strategy |
|--------------|----------|-------------|----------------|
| API Failure | `fetch_users_from_api` | 2% | 3 attempts with exponential backoff |
| DB Failure | `insert_users_to_staging` | 40% | 10 attempts with fast backoff (0.1s) |
| OOM Error | `extract_and_load_workflow` | 5% (after batch 5) | Workflow recovery from checkpoint |

### Retry Configuration Examples

```python
# API step with retries
@DBOS.step(retries_allowed=True, max_attempts=3)
def fetch_users_from_api(...):
    ...

# Database step with aggressive retries
@DBOS.step(retries_allowed=True, max_attempts=10, backoff_rate=0.1, interval_seconds=0.1)
def insert_users_to_staging(...):
    ...

# Workflow with recovery
@DBOS.workflow(max_recovery_attempts=100)
def extract_and_load_workflow(...):
    ...
```

## Workflow Monitoring

### Using the Client

```bash
# Check specific workflow
python client.py status <workflow-id>

# List recent workflows
python client.py list limit=20

# Filter by status
python client.py list status=SUCCESS
python client.py list status=ERROR
```

### DBOS Admin Interface

Access the DBOS admin interface (if enabled):
```
http://localhost:3001
```

## Configuration

### DBOS Configuration

The server uses the following DBOS configuration:

```python
config = {
    "name": "elt-pipeline",
    "database_url": os.getenv("DBOS_DATABASE_URL"),
    "log_level": "DEBUG",
}
```

### Schedule Configuration

To change the schedule, modify the cron expression in `elt.py`:

```python
@DBOS.scheduled("20 5 * * *")  # Current: Daily at 5:20 AM GMT
@DBOS.workflow()
def scheduled_elt_trigger(scheduled_time, actual_time):
    ...
```

Cron format: `minute hour day month dayOfWeek`

Examples:
- `"*/5 * * * *"` - Every 5 minutes
- `"0 * * * *"` - Every hour
- `"0 0 * * *"` - Daily at midnight
- `"0 0 * * 0"` - Weekly on Sunday

### Batch Configuration

Adjust batch sizes in workflow calls:

```python
# Default: 10 batches × 10 pages = 100 pages
extract_and_load_workflow(
    organization_id=org_id,
    connected_integration_id=integration_id,
    num_batches=10,  # Number of batches
    batch_size=10,   # Pages per batch
)
```

## Testing

### Run the Test Script

The easiest way to test the complete ELT pipeline:

```bash
python test_elt.py
```

This script will:
1. Initialize a fresh database with test data
2. Run a complete ELT pipeline for one org/integration
3. Display results from all tables (staging, CDC, latest)
4. Verify the pipeline worked correctly

Expected output:
```
🧪 Testing ELT Pipeline
============================================================
📦 Initializing database...
✅ Database initialized
🌱 Seeding connected integrations...
✅ Seeded 2 integrations
🚀 Launching DBOS...
🔄 Running ELT pipeline...
✅ ELT Pipeline Completed Successfully!
📈 Results:
   Users loaded (staging): 1000
   CDC changes detected: 1000 (1000 inserts, 0 updates)
   Applied to latest: 1000 changes
   Latest table records: 1000
   Synced to Postgres: 1000 changes
```

### Test Idempotency

To verify the pipeline handles workflow replays without creating duplicates:

```bash
python test_idempotency.py
```

This script will:
1. Run the ELT pipeline with a fixed workflow_id
2. Run it AGAIN with the same workflow_id (simulating crash/replay)
3. Verify no duplicate records were created
4. Confirm idempotency guarantees

Expected output:
```
🧪 Testing ELT Pipeline Idempotency
============================================================
🔄 FIRST RUN - Running ELT pipeline
✅ First run completed!

🔄 SECOND RUN - Simulating workflow replay with SAME workflow_id
✅ Second run completed!

🔍 IDEMPOTENCY VERIFICATION
1️⃣  Checking if results are identical...
   ✅ Users loaded count matches
2️⃣  Checking CDC table for duplicates...
   ✅ CDC table unchanged: 1000 records (no duplicates!)
3️⃣  Checking Latest table for duplicates...
   ✅ Latest table unchanged: 1000 records (no duplicates!)

🎉 ALL CHECKS PASSED! Pipeline is IDEMPOTENT!
```

### Manual Testing

Run workflows manually for testing:

```python
from elt import root_orchestration_workflow, elt_pipeline_workflow
from dbos import DBOS

# Run a single ELT pipeline
result = elt_pipeline_workflow(
    organization_id="org-001",
    connected_integration_id="<uuid-here>"
)
print(result)

# Run the full pipeline for all integrations
result = root_orchestration_workflow()
print(result)
```

### Using the Client

Or use the client for remote testing:

```bash
# Test a single org/integration
python client.py start elt_pipeline_workflow \
    organization_id=org-001 \
    connected_integration_id=<uuid-here>

# Test all integrations
python client.py start root_orchestration_workflow
```

### Inspecting the Database

After running the pipeline, inspect the tables:

```python
from db import get_user_count

# Check staging table
staging_count = get_user_count(table_name="users_staging")
print(f"Staging: {staging_count} records")

# Check CDC table
cdc_count = get_user_count(table_name="users_cdc")
print(f"CDC: {cdc_count} changes")

# Check latest table
latest_count = get_user_count(table_name="users_latest")
print(f"Latest: {latest_count} records")
```

## Key Files Explained

### `elt.py`
Main workflow definitions including:
- DBOS steps for API fetching and database insertion
- Sub-workflows for each ELT stage
- Main ELT pipeline orchestration
- Root workflow for processing all integrations
- Scheduled workflow trigger

### `server.py`
DBOS server implementation:
- DBOS initialization and configuration
- Database setup and seeding
- Health check HTTP server (port 8080)
- Graceful shutdown handling
- Multiprocess coordination

### `client.py`
Command-line client for remote workflow triggering:
- Generic parameter parsing (auto-type conversion)
- Workflow enqueueing via DBOSClient
- Status checking and result retrieval
- Workflow listing with filters

### `data.py`
Data models and generation:
- `User` and `ConnectedIntegration` dataclasses
- Faker-based fake data generation
- Stable UUID generation from external IDs

### `db.py`
Database operations:
- SQLite database and table creation
- Connected integrations seeding
- User insertion with batch support
- Deduplication via SQL window functions

## Idempotency and Duplication Prevention

⚠️ **CRITICAL:** The pipeline is designed to be **duplication-proof** when workflows crash and replay.

Key mechanisms:
- **Staging Table**: Window functions deduplicate retry-induced duplicates
- **CDC Table**: Delete-before-insert ensures no duplicate change records
- **Latest Table**: `INSERT OR REPLACE` provides upsert semantics
- **Workflow Recovery**: DBOS guarantees steps won't re-execute on replay
- **Multi-Tenancy**: Composite keys ensure isolation per organization/integration

For detailed explanation, see [IDEMPOTENCY.md](IDEMPOTENCY.md) and [MULTI_TENANCY.md](MULTI_TENANCY.md).

### Quick Example

```python
from dbos import SetWorkflowID

# Same workflow_id = idempotent operation
with SetWorkflowID("test-workflow-001"):
    result1 = elt_pipeline_workflow(org_id, integration_id)

# Simulate crash and replay - produces same result
with SetWorkflowID("test-workflow-001"):
    result2 = elt_pipeline_workflow(org_id, integration_id)

assert result1 == result2  # ✅ No duplicates!
```

## Production Considerations

### Scaling

- **Queue Concurrency**: Adjust `Queue("elt_queue", concurrency=5)` for parallelism
- **Batch Size**: Tune `num_batches` and `batch_size` based on available memory
- **Database**: Use connection pooling for high throughput
- **Monitoring**: Integrate with OpenTelemetry for distributed tracing

### Error Handling

- All transient failures are automatically retried
- Permanent failures are logged with workflow status `ERROR`
- Use `DBOS.list_workflows(status="ERROR")` to find failed workflows
- Resume failed workflows with `DBOS.resume_workflow(workflow_id)`

### Data Consistency

- **Idempotent operations** prevent duplicates on replay (see [IDEMPOTENCY.md](IDEMPOTENCY.md))
- Deduplication handles retry-induced duplicates automatically
- Composite primary key prevents constraint violations
- Window functions ensure latest data is used
- Workflow IDs track data provenance

## Troubleshooting

### Server won't start

Check PostgreSQL connection:
```bash
psql $DBOS_DATABASE_URL
```

### Workflows failing immediately

Check logs for configuration errors:
```bash
python server.py  # Look for DBOS initialization errors
```

### High memory usage

Reduce batch sizes:
```python
num_batches=20, batch_size=5  # More batches, smaller size
```

### Duplicate data

The window function should handle this automatically. Verify with:
```python
from db import get_unique_user_count, get_user_count

total = get_user_count()
unique = get_unique_user_count()
print(f"Total: {total}, Unique: {unique}, Duplicates: {total - unique}")
```

## Resources

- [DBOS Documentation](https://docs.dbos.dev/)
- [Architecture Documentation](./ARCHITECTURE.md)
- [DBOS Python SDK](https://github.com/dbos-inc/dbos-transact-py)

## License

See repository root for license information.
