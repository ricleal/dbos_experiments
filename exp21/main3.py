import random
from contextlib import asynccontextmanager

import psutil
import uvicorn
from dbos import DBOS, DBOSConfig, Queue, WorkflowHandleAsync
from fastapi import FastAPI

"""
# start httpbin docker container
docker pull kennethreitz/httpbin
docker run -p 8080:80 kennethreitz/httpbin

# start the server:
uv run fastapi dev ./exp21/main3.py


LAST=$(date +%s.%N)
while true; do
  http localhost:8000/health | jq '.memory_mb'
  NOW=$(date +%s.%N)
  ELAPSED=$(echo "$NOW - $LAST" | bc)
  echo -n "$(date +"%T") - Elapsed: ${ELAPSED}s - "
  LAST=$(date +%s.%N)
  sleep 1
done

This shows the of calling sync http requests inside DBOS async steps.
FastAPI server is blocked and not responsive to health checks while steps are running.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config: DBOSConfig = {
        "name": "dbos-starter",
        "system_database_url": "postgresql://trustle:trustle@localhost:5432/test_dbos_sys?sslmode=disable",
        "run_admin_server": False,
        "enable_otlp": False,
    }
    DBOS(config=config)
    DBOS.launch()

    yield

    # Shutdown
    DBOS.destroy(workflow_completion_timeout_sec=10)


app = FastAPI(lifespan=lifespan)


queue = Queue("example-queue")


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


@DBOS.step()
async def dbos_step(n: int) -> int:
    DBOS.logger.info(f"Step {n} started")
    t = random.uniform(1, 5)
    # sync request to httpbin
    import requests

    response = requests.get(f"http://localhost:8080/delay/{t}")
    DBOS.logger.info(f"Step {n} httpbin response status: {response.status_code}")
    DBOS.logger.info(f"Step {n} completed!")
    return n


@DBOS.workflow()
async def dbos_workflow(n_steps: int) -> list[int]:
    DBOS.logger.info(f"Starting workflow n_steps={n_steps}")
    step_results = []
    for i in range(n_steps):
        result = await dbos_step(i)
        step_results.append(result)
    DBOS.logger.info(f"Stopping workflow n_steps={n_steps}")
    return step_results


@app.get("/")
@DBOS.workflow()
async def dbos_root_workflow():
    DBOS.logger.info("Starting root workflow")
    handles = []
    for i in range(1, 6):
        handle: WorkflowHandleAsync = await queue.enqueue_async(dbos_workflow, i)
        handles.append(handle)
    # results = [await handle.get_result() for handle in handles]
    # DBOS.logger.info("Root workflow completed")
    # return {"status": "completed", "results": results}

    # let's not block the root workflow and return the status if each handle
    statuses = [await handle.get_status() for handle in handles]
    DBOS.logger.info("Root workflow completed")
    return {"status": "completed", "handles_status": statuses}


DBOS.launch()

# run with: fastapi dev main.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
