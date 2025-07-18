import datetime
import logging
import sys
import time

from dbos import DBOS, WorkflowHandle, WorkflowStatus
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


app = FastAPI()
DBOS(fastapi=app)


logger = logging.getLogger("exp6")
logger.setLevel(DBOS.logger.level)
logger.addHandler(log_handler)

app_name = "exp6-scope"


@DBOS.dbos_class()
class A:

    counter = 0

    def __init__(self, instance_id: str):
        self.instance_id = instance_id

    @DBOS.step()
    def step(self, step_number: int = 0):
        global app_name
        logger.info(
            dict(
                message="instance step",
                instance_id=self.instance_id,
                app_name=app_name,
                step_number=step_number,
            )
        )
        self.counter += 1
        time.sleep(0.5)

    @staticmethod
    @DBOS.workflow()
    def workflow():
        global app_name

        logger.info(dict(message="Starting Workflow", app_name=app_name))

        a = A(datetime.datetime.now().isoformat())
        for i in range(30):
            a.step(i)

        logger.info(dict(message="Finished Workflow", app_name=app_name))


@app.post(
    "/trigger_sync",
    summary="Start a workflow",
    description="Start a workflow",
)
def trigger_sync():
    logger.info(dict(message="Starting Main", app_name=app_name))
    A.workflow()
    logger.info(dict(message="Finished Main", app_name=app_name))
    return JSONResponse(content=dict(message="workflow ran successfully"))


@DBOS.workflow()
def start_async_workflow():
    logger.info(dict(message="Starting Async Main", app_name=app_name))
    A.workflow()
    logger.info(dict(message="Finished Async Main", app_name=app_name))


@app.post(
    "/trigger_async",
    summary="Start an Async workflow",
    description="Start an Async workflow",
)
def trigger_async():
    handle: WorkflowHandle = DBOS.start_workflow(start_async_workflow)
    status: WorkflowStatus = handle.get_status()
    if not status:
        raise HTTPException(status_code=404, detail="workflow failed to start")
    return JSONResponse(
        content=dict(wf_status=status.__dict__, workflow_id=handle.workflow_id)
    )
