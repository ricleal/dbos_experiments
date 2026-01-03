import asyncio
import logging
import random
from contextlib import asynccontextmanager

import uvicorn
from dbos import DBOS, DBOSConfig, Queue, WorkflowHandleAsync
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s ->> %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config: DBOSConfig = {
        "name": "dbos-starter",
        "system_database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        "run_admin_server": False,
        "application_version": "0.1.0",
        "executor_id": "exp22-executor-1",
        "enable_otlp": False,
    }
    DBOS(config=config)
    DBOS.launch()
    logger.info("Application started")

    yield

    # Shutdown
    logger.info("FastAPI shutdown event triggered")
    logger.info("Closing DBOS connections...")
    DBOS.destroy(workflow_completion_timeout_sec=10)
    logger.info("Graceful shutdown complete")


app = FastAPI(lifespan=lifespan)

queue = Queue("example-queue")


@DBOS.step()
async def dbos_step(n: int) -> int:
    DBOS.logger.info(f"{DBOS.workflow_id} :: \t Step {n}")
    t = random.random() * 0.5
    await asyncio.sleep(t)
    return n


@DBOS.workflow()
async def dbos_sub_workflow(id: int, n_steps: int) -> list[int]:
    DBOS.logger.info(f"{DBOS.workflow_id} :: Starting sub-workflow {id}")
    step_results = []
    for i in range(n_steps):
        result = await dbos_step(i)
        step_results.append(result)
    DBOS.logger.info(f"{DBOS.workflow_id} :: Sub-workflow {id} completed")
    return step_results


@DBOS.workflow()
async def dbos_workflow(
    n_sub_workflows: int, n_steps_per_workflow: int
) -> list[list[int]]:
    DBOS.logger.info(f"{DBOS.workflow_id} :: Starting workflow")
    workflow_results = []
    for i in range(n_sub_workflows):
        result = await dbos_sub_workflow(i, n_steps_per_workflow)
        workflow_results.append(result)
    DBOS.logger.info(f"{DBOS.workflow_id} :: Workflow completed")
    return workflow_results


@app.get("/")
async def handle_request(n_sub_workflows: int = 6, n_steps_per_workflow: int = 5):
    logger.info(
        f"Enqueuing workflow with sub-workflows: {n_sub_workflows}, steps per workflow: {n_steps_per_workflow}"
    )
    handle: WorkflowHandleAsync = await queue.enqueue_async(
        dbos_workflow, n_sub_workflows, n_steps_per_workflow
    )
    status = await handle.get_status()
    return {"status": "completed", "workflow_status": status.__dict__}


# This runs the app with: python exp22/main.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
