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

## Conclusion

DBOS with FastAPI is suitable for production deployments requiring health checks and liveness probes. The application remains responsive to monitoring requests even under workflow load.
