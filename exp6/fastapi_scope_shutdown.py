import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from dbos import DBOS, Queue, WorkflowHandle, WorkflowStatus
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pythonjsonlogger.json import JsonFormatter

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.addHandler(log_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # put before the yield the startup code
    DBOS.launch()
    yield
    # put after the yield the shutdown code
    DBOS.destroy()


app = FastAPI(lifespan=lifespan)
DBOS(fastapi=app)


logger = logging.getLogger("exp6")
logger.setLevel(DBOS.logger.level)
logger.addHandler(log_handler)

app_name = "exp6-scope"


# queue = Queue("example_queue", concurrency=5, limiter={"limit": 10, "period": 10})


# crontabl every 5 seconds
@DBOS.scheduled("*/5 * * * * *")
@DBOS.workflow()
def example_scheduled_workflow(scheduled_time: datetime, actual_time: datetime):
    logger.info(
        dict(
            message="Scheduled workflow started",
            app_name=app_name,
            id=DBOS.workflow_id,
            pid=os.getpid(),
            scheduled_time=scheduled_time.isoformat(),
            actual_time=actual_time.isoformat(),
        )
    )


queue = Queue("example_queue")


@DBOS.step()
def step(step_number: int = 0):
    global app_name
    logger.info(
        dict(
            message="step started",
            app_name=app_name,
            step_number=step_number,
            id=DBOS.workflow_id,
        )
    )

    # calculate fibonacci of the step number
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n - 1) + fib(n - 2)

    result = fib(step_number)

    logger.info(
        dict(
            message="step completed",
            app_name=app_name,
            step_number=step_number,
            result=result,
            id=DBOS.workflow_id,
        )
    )


@DBOS.workflow()
def workflow():
    global app_name

    logger.info(dict(message="Starting Workflow", app_name=app_name))

    handles = []
    for i in range(50):

        handle: WorkflowHandle = queue.enqueue(step, i)
        handles.append(handle)
        status: WorkflowStatus = handle.get_status()
        if not status:
            raise HTTPException(status_code=404, detail="workflow failed to start")
        logger.info(
            dict(
                message="Enqueued step",
                step_number=i,
                app_name=app_name,
                workflow_id=handle.workflow_id,
            )
        )

    for handle in handles:
        result: WorkflowStatus = handle.get_result()
        logger.info(
            dict(
                message="Completed step",
                step_number=handle.args[0],
                app_name=app_name,
                workflow_id=handle.workflow_id,
                result=result.__dict__,
            )
        )

    logger.info(dict(message="Finished Workflow", app_name=app_name))


@app.post(
    "/shutdown",
    summary="Shutdown the application",
    description="Shutdown the application",
)
def shutdown():
    # Kill -9 -1
    sys.exit(0)


@app.post(
    "/trigger_async",
    summary="Start an Async workflow",
    description="Start an Async workflow",
)
def trigger_async():
    handle: WorkflowHandle = DBOS.start_workflow(workflow)
    status: WorkflowStatus = handle.get_status()
    if not status:
        raise HTTPException(status_code=404, detail="workflow failed to start")
    return JSONResponse(
        content=dict(wf_status=status.__dict__, workflow_id=handle.workflow_id)
    )
