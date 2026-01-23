# Experiment 21: DBOS FastAPI Health Checks During Workflow Execution

## Overview

This experiment tests whether a DBOS FastAPI application can respond to health checks while running workflows. **Result: It can!**

The application remains responsive to HTTP requests even when workflows are actively executing in the background.

## Test Setup

- FastAPI endpoint at `/` that enqueues 5 workflows
- Each workflow runs multiple steps with random delays (1-5 seconds)
- Health check endpoint at `/health` that reports memory usage
- Continuous health probing while workflows execute

## Health Probe

Run this in a separate terminal to continuously monitor the application:

```bash
while true; do http localhost:8000/health; sleep 1; done
```

## Results

### Health Check Response

```json
{
    "memory_mb": 89.75,
    "status": "ok"
}
```

### Observations

✅ **Responsive**: Application replies to all health check pings while workflows run  
✅ **Low Memory**: ~90 MB memory usage during workflow execution  
✅ **Non-blocking**: FastAPI endpoints remain available despite background processing  

## How It Works

1. DBOS runs workflows in background threads/tasks
2. FastAPI event loop remains free to handle HTTP requests
3. Queue-based workflow execution doesn't block the web server
4. Health checks return immediately with current memory status

## Files

- **`main.py`**: Original test with simulated delays using `asyncio.sleep()`
- **`main2.py`**: Real CPU-intensive work using recursive Fibonacci calculations
- **`main3.py`**: **Async endpoints** - Demonstrates FastAPI unresponsiveness with async workflows and endpoints
- **`main4.py`**: **Sync endpoints** - Demonstrates FastAPI responsiveness when using sync endpoints with proper lifespan management

## Key Findings

### FastAPI Responsiveness with Async vs Sync

**Important Discovery**: When using DBOS async workflows with FastAPI async endpoints, the server becomes unresponsive to health checks during workflow execution. **Solution**: Use sync endpoints.

#### main3.py (Async - Unresponsive ❌)

- Uses `async def` for endpoints and workflows
- FastAPI event loop gets blocked by DBOS async workflow execution
- Health check endpoint becomes unresponsive while workflows run
- Problem: `await queue.enqueue_async()` blocks the event loop

#### main4.py (Sync - Responsive ✅)

- Uses `def` (sync) for endpoints and workflows
- FastAPI remains fully responsive to health checks
- Workflows run in background without blocking the server
- Uses proper FastAPI lifespan management for DBOS initialization/cleanup
- Makes HTTP requests to httpbin container for realistic external API simulation

**Recommendation**: Use sync endpoints and workflows when you need FastAPI to remain responsive to health checks and other requests while workflows execute.

## Monitoring Command

Enhanced health check monitoring with response time tracking:

```bash
LAST=$(date +%s.%N)
while true; do
  http localhost:8000/health | jq '.memory_mb'
  NOW=$(date +%s.%N)
  ELAPSED=$(echo "$NOW - $LAST" | bc)
  echo -n "$(date +"%T") - Elapsed: ${ELAPSED}s - "
  LAST=$(date +%s.%N)
  sleep 1
done
```

## Running the Experiment

### With Simulated Delays (main.py)

1. Start the server:
```bash
python exp21/main.py
```

2. In another terminal, start the health probe:
```bash
while true; do http localhost:8000/health; sleep 1; done
```

3. Trigger workflows:
```bash
http localhost:8000/
```

4. Observe health checks continuing to respond while workflows execute

### With CPU-Intensive Work (main2.py)

1. Start the server:
```bash
python exp21/main2.py
```

2. Start the health probe in another terminal (same as above)

3. Trigger workflows that calculate Fibonacci numbers (30+):
```bash
http localhost:8000/
```

4. Monitor health checks and memory usage while CPU-intensive calculations run

### With Async Endpoints - Demonstrating Unresponsiveness (main3.py)

1. Start the server:
```bash
uv run fastapi dev exp21/main3.py
```

2. In another terminal, start the health probe with timing:
```bash
LAST=$(date +%s.%N)
while true; do
  http localhost:8000/health | jq '.memory_mb'
  NOW=$(date +%s.%N)
  ELAPSED=$(echo "$NOW - $LAST" | bc)
  echo -n "$(date +"%T") - Elapsed: ${ELAPSED}s - "
  LAST=$(date +%s.%N)
  sleep 1
done
```

3. Trigger workflows:
```bash
http localhost:8000/
```

4. **Observe**: Health checks will hang/timeout while async workflows execute

### With Sync Endpoints - Demonstrating Responsiveness (main4.py)

**Prerequisites**: Start httpbin container for external API simulation:
```bash
docker pull kennethreitz/httpbin
docker run -p 8080:80 kennethreitz/httpbin
```

1. Start the server:
```bash
uv run fastapi dev exp21/main4.py
```

2. Start the health probe (same as above)

3. Trigger workflows:
```bash
http localhost:8000/
```

4. **Observe**: Health checks continue to respond immediately even while workflows execute

## Conclusion

DBOS with FastAPI is suitable for production deployments requiring health checks and liveness probes, **but you must use sync endpoints and workflows**. 

The application remains responsive to monitoring requests even under workflow load when properly configured with:
- Sync (`def`) endpoint definitions instead of async (`async def`)
- Sync workflow and step definitions
- Proper FastAPI lifespan management for DBOS initialization
- Background queue-based workflow execution

**Critical Insight**: Async endpoints with DBOS async workflows can block the FastAPI event loop, making the server unresponsive. Always prefer sync endpoints for production services that need to maintain responsiveness during workflow execution.
