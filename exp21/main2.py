import asyncio

import psutil
import uvicorn
from dbos import DBOS, DBOSConfig, Queue, WorkflowHandleAsync
from fastapi import FastAPI

app = FastAPI()
config: DBOSConfig = {
    "name": "dbos-starter",
    "system_database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)

queue = Queue("example-queue")


def fibonacci(n: int) -> int:
    """Calculate Fibonacci number recursively (CPU-intensive)"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@app.get("/health")
async def health_check():
    """Health check endpoint to monitor memory usage
    I run this: `while true; do http localhost:8000/health; sleep 1; done`
    or `while true; do echo -n "$(date +"%T") - "; http localhost:8000/health | jq '.memory_mb'; sleep 1; done`
    in another terminal to see memory usage over time.
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024  # Convert bytes to MB
    return {
        "status": "ok",
        "memory_mb": round(memory_mb, 2),
    }


@DBOS.step(retries_allowed=True)
async def dbos_step(n: int) -> dict:
    DBOS.logger.info(f"Starting Fibonacci calculation for n={n}")
    # Run CPU-intensive work in thread pool to avoid blocking
    # Allocate memory to simulate high memory usage
    _ = bytearray(10**8)  # Allocate ~100MB
    result = await asyncio.to_thread(fibonacci, n)
    DBOS.logger.info(f"Fibonacci({n}) = {result}")
    return {"n": n, "fibonacci": result}


@DBOS.workflow(max_recovery_attempts=2)
async def dbos_workflow(n_steps: int) -> list[dict]:
    DBOS.logger.info(f"Starting workflow with {n_steps} Fibonacci calculations")
    step_results = []
    # Calculate Fibonacci for numbers 30, 31, 32, etc. (CPU intensive)
    base_number = 30
    for i in range(n_steps):
        result = await dbos_step(base_number + i)
        step_results.append(result)
    DBOS.logger.info("Workflow completed")
    return step_results


@app.get("/")
@DBOS.workflow(max_recovery_attempts=2)
async def dbos_root_workflow():
    DBOS.logger.info("Starting root workflow")
    handles = []
    # Enqueue 5 workflows, each calculating 1-5 Fibonacci numbers
    for i in range(1, 6):
        handle: WorkflowHandleAsync = await queue.enqueue_async(dbos_workflow, i)
        handles.append(handle)

    # Return handle statuses without blocking
    statuses = [await handle.get_status() for handle in handles]
    DBOS.logger.info("Root workflow completed")
    return {"status": "completed", "handles_status": statuses}


DBOS.launch()

# run with: python main2.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
