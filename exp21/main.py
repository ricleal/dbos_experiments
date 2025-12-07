import asyncio
import random

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
    DBOS.logger.info(f"Starting step {n}")
    t = random.uniform(1, 5)
    # await DBOS.sleep_async(t)
    await asyncio.sleep(t)
    DBOS.logger.info(f"Step {n} completed!")
    return n


@DBOS.workflow()
async def dbos_workflow(n_steps: int) -> list[int]:
    DBOS.logger.info("Starting workflow")
    step_results = []
    for i in range(n_steps):
        result = await dbos_step(i)
        step_results.append(result)
    DBOS.logger.info("Workflow completed")
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
