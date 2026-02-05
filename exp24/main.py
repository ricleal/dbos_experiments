import logging
import random
import time
from contextlib import asynccontextmanager

import uvicorn
from dbos import DBOS, DBOSConfig, Queue, SetEnqueueOptions, WorkflowHandle
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s ->> %(message)s", datefmt="%H:%M:%S")
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
    DBOS.destroy(workflow_completion_timeout_sec=10)
    logger.info("Graceful shutdown complete")


app = FastAPI(lifespan=lifespan)

queue = Queue("example-queue")


@DBOS.step(retries_allowed=True, max_attempts=3)
def dbos_step(n: int) -> int:
    s = DBOS.step_status
    DBOS.logger.info(f"\t\t{DBOS.workflow_id}::{s.step_id} :: \t Step {n} - Attempt {s.current_attempt}/{s.max_attempts}")
    t = random.random() * 0.5
    time.sleep(t)

    if n == 3:
        # Raise exception for demonstration
        # raise ValueError("Simulated error in step")

        # Simulate OOM error
        import ctypes

        ctypes.string_at(0)
    return n


@DBOS.workflow(max_recovery_attempts=2)
def dbos_sub_workflow(id: int, n_steps: int) -> list[int]:
    DBOS.logger.info(f"\t{DBOS.workflow_id} :: Starting sub-workflow {id}")
    step_results = []
    for i in range(n_steps):
        result = dbos_step(i)
        step_results.append(result)
        DBOS.sleep(0.1)
        # Show queue
        workflows = DBOS.list_queued_workflows(load_input=False)
        for idx, wf in enumerate(workflows):
            DBOS.logger.info(f"\t* {idx}: Queued workflow: {wf.workflow_id} :: {wf.name}:{wf.status} - {wf.recovery_attempts}")

    DBOS.logger.info(f"\t{DBOS.workflow_id} :: Sub-workflow {id} completed")
    return step_results


@DBOS.workflow(max_recovery_attempts=2)
def dbos_workflow(n_sub_workflows: int, n_steps_per_workflow: int) -> list[list[int]]:
    DBOS.logger.info(f"{DBOS.workflow_id} :: Starting workflow")
    workflow_results = []
    for i in range(n_sub_workflows):
        result = dbos_sub_workflow(i, n_steps_per_workflow)
        workflow_results.append(result)
        DBOS.sleep(0.1)
    DBOS.logger.info(f"{DBOS.workflow_id} :: Workflow completed")
    return workflow_results


@app.get("/")
def handle_request(n_sub_workflows: int = 6, n_steps_per_workflow: int = 5):
    logger.info(f"Enqueuing workflow with sub-workflows: {n_sub_workflows}, steps per workflow: {n_steps_per_workflow}")

    dedup_id = f"{n_sub_workflows}/{n_steps_per_workflow}"
    try:
        with SetEnqueueOptions(deduplication_id=dedup_id):
            handle: WorkflowHandle = queue.enqueue(dbos_workflow, n_sub_workflows, n_steps_per_workflow)
    except Exception as e:
        logger.exception("Failed to enqueue workflow")
        return {"status": "error", "message": str(e)}

    status = handle.get_status()
    return {"status": "completed", "workflow_status": status.__dict__}


@app.get("/queue")
def handle_queue():
    workflows = DBOS.list_queued_workflows(load_input=False)
    return {"queued_workflows": [wf.__dict__ for wf in workflows]}


# This runs the app with: python exp22/main.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
