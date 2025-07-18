import datetime
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import List

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

credentials_cache = {}


def get_credentials():
    global credentials_cache
    if "credentials" not in credentials_cache:
        logger.info(dict(message="fetching credentials"))
        credentials_cache["credentials"] = datetime.datetime.now().isoformat()
    return credentials_cache["credentials"]


@DBOS.step()
def describe_user(user_id: str):
    credentials = get_credentials()
    logger.info(
        dict(
            message="describe_user",
            user_id=user_id,
            credentials=credentials,
            app_name=app_name,
        )
    )


@DBOS.workflow()
def get_users_page(page: List[str]):
    credentials = get_credentials()
    for user_id in page:
        describe_user(user_id)
        logger.info(
            dict(
                message="get_users_page",
                user_id=user_id,
                credentials=credentials,
                app_name=app_name,
            )
        )


@DBOS.workflow()
def get_users():
    credentials = get_credentials()
    logger.info(dict(message="get_users", credentials=credentials, app_name=app_name))
    for i in range(5):
        get_users_page([f"user_{i}_{j}" for j in range(3)])
        time.sleep(0.5)


@app.post(
    "/trigger_async",
    summary="Start an Async workflow",
    description="Start an Async workflow",
)
def trigger_async():
    handle: WorkflowHandle = DBOS.start_workflow(get_users)
    status: WorkflowStatus = handle.get_status()
    if not status:
        raise HTTPException(status_code=404, detail="workflow failed to start")
    return JSONResponse(
        content=dict(wf_status=status.__dict__, workflow_id=handle.workflow_id)
    )
