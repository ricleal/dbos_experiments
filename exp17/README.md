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

### `users`

Staging table for extracted users (supports duplicates for idempotency):

```sql
CREATE TABLE users (
    id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    connected_integration_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at DATETIME DEFAULT(datetime('subsec')),
    PRIMARY KEY (id, workflow_id, created_at)
)
```

The composite primary key allows duplicates while enabling efficient deduplication.

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

Run workflows manually for testing:

```python
from elt import root_orchestration_workflow
from dbos import DBOS

# Run the full pipeline
result = root_orchestration_workflow()
print(result)
```

Or use the client:

```bash
python client.py start root_orchestration_workflow
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
