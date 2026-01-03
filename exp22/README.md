# Exp22: DBOS Graceful Shutdown Example

This example demonstrates how to implement graceful shutdown for DBOS applications with FastAPI, ensuring that workflows complete properly before the application terminates.

## Overview

This application showcases:
- **Graceful shutdown** using FastAPI's lifespan context manager
- **Async workflows** with nested sub-workflows and steps
- **Queue-based workflow execution** for background processing
- **Proper cleanup** of DBOS connections and resources

## Key Features

### Graceful Shutdown Implementation

The application uses FastAPI's `lifespan` context manager to handle startup and shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    DBOS(config=config)
    DBOS.launch()
    logger.info("Application started")
    
    yield
    
    # Shutdown
    logger.info("FastAPI shutdown event triggered")
    logger.info("Closing DBOS connections...")
    DBOS.destroy(workflow_completion_timeout_sec=10)
    logger.info("Graceful shutdown complete")
```

The `DBOS.destroy(workflow_completion_timeout_sec=10)` call ensures:
- All running workflows have up to 10 seconds to complete
- Database connections are properly closed
- Resources are cleaned up gracefully

### Workflow Architecture

The application demonstrates a nested workflow pattern:
- **Main workflow** (`dbos_workflow`): Orchestrates multiple sub-workflows
- **Sub-workflows** (`dbos_sub_workflow`): Execute a series of steps
- **Steps** (`dbos_step`): Perform individual operations with random delays

All workflows are enqueued on a queue for managed concurrency.

## Running the Example

### Prerequisites

- PostgreSQL database running at `localhost:5432`
- Database credentials: `trustle:trustle`
- Database name: `test`

### Start the application

```bash
python -m exp22.main
```

The server will start on `http://localhost:8000`

### Test the endpoint

```bash
# Default: 6 sub-workflows, 5 steps each
curl http://localhost:8000/

# Custom parameters
curl "http://localhost:8000/?n_sub_workflows=2&n_steps_per_workflow=3"
```

### Test graceful shutdown

```bash
# Start a workflow and then send shutdown signal
http localhost:8000/?n_sub_workflows=2 && sleep 1 && pkill -TERM -f "python -m exp22.main"
```

## Expected Behavior

1. **During execution**: Workflows and steps log their progress with time-only timestamps
2. **On shutdown signal (SIGTERM)**: 
   - FastAPI triggers the lifespan shutdown
   - DBOS waits up to 10 seconds for workflows to complete
   - Connections are closed gracefully
   - Application exits cleanly

## Configuration

The application is configured with:
- **Application name**: `dbos-starter`
- **Application version**: `0.1.0`
- **Executor ID**: `exp22-executor-1`
- **Admin server**: Disabled
- **OpenTelemetry**: Disabled
- **Workflow completion timeout**: 10 seconds

## Logging

Logs use a simplified time-only format (`HH:MM:SS`) for easier readability during testing and debugging.


## TODO:  Graceful Shutdown for Kubernetes with DBOS and Uvicorn

## The Problem

When running Uvicorn-based applications in Kubernetes with an Application Load Balancer (ALB):

1. **Kubernetes sends SIGTERM** to initiate pod shutdown
2. **ALB takes time to deregister** the pod (typically 10-30 seconds)
3. **Default Uvicorn behavior**: Immediately stops accepting new connections upon receiving SIGTERM
4. **Result**: ALB continues routing traffic to the pod, causing "connection refused" errors

THere's a PR to address this:
https://github.com/Kludex/uvicorn/pull/2242

