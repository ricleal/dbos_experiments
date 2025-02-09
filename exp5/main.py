import logging
import sys
import uuid
from enum import Enum
from typing import Dict

from dbos import DBOS, Queue, SetWorkflowID, WorkflowHandle, WorkflowStatus
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import insert, select
from sqlalchemy.engine.cursor import CursorResult

from .models import Accesses, Errors

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.handlers = [log_handler]


class Status(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    canceled = "canceled"


app = FastAPI()
DBOS(fastapi=app)

EVENT_KEY = "event_key"


# it may not start more than 50 functions in 30 seconds
queue = Queue("example_queue", concurrency=10, limiter={"limit": 50, "period": 30})


@DBOS.transaction()
def process_task(task: dict):
    DBOS.span.set_attributes(task)
    result: CursorResult = DBOS.sql_session.execute(
        insert(Accesses).values(user_id=task["user_id"], status=Status.requested)
    )
    DBOS.logger.info(dict(message="Workflow step transaction", rows=result.rowcount))


@DBOS.transaction()
def process_error(error: Dict[str, str]):
    DBOS.span.set_attribute("error", error)
    result: CursorResult = DBOS.sql_session.execute(
        insert(Errors).values(message=error)
    )
    DBOS.logger.error(dict(message="Workflow error transaction", rows=result.rowcount))


@DBOS.workflow()
def process_tasks(tasks: dict):
    DBOS.logger.info(f"I am a workflow with ID {DBOS.workflow_id}")
    DBOS.set_event(EVENT_KEY, DBOS.workflow_id)
    task_handles = []
    # Enqueue each task so all tasks are processed concurrently.
    for task in tasks:
        DBOS.span.set_attributes({"task": str(task)})
        handle: WorkflowHandle = queue.enqueue(process_task, dict(user_id=task))
        task_handles.append(handle)
    # Wait for each task to complete and retrieve its result.
    # Return the results of all tasks.
    for handle in task_handles:
        try:
            res = handle.get_result()
            DBOS.span.set_attribute("task_result", str(res))
        except Exception as e:
            m = dict(
                message="Task failed",
                wf_id=handle.get_workflow_id(),
                status=handle.get_status().status,
            )
            process_error(m | {"error": str(e)})
            DBOS.logger.exception(m)
            continue
        DBOS.logger.info(
            dict(
                message="Task completed",
                wf_id=handle.get_workflow_id(),
                status=handle.get_status(),
                result=res,
            )
        )


@app.post(
    "/submit",
    summary="Start a workflow",
    description="Start a workflow with a list of user ids",
)
def fastapi_endpoint():
    DBOS.span.set_attribute("endpoint", "submit")
    wfid = str(uuid.uuid4())
    with SetWorkflowID(wfid):
        handle: WorkflowHandle = DBOS.start_workflow(
            process_tasks,
            [
                "00000000-0000-0000-0000-000000000000",
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                "00000000-0000-0000-0000-000000000003",
            ],
        )

    status: WorkflowStatus = handle.get_status()
    event = DBOS.get_event(handle.workflow_id, EVENT_KEY)
    if not status:
        raise HTTPException(status_code=404, detail="workflow failed to start")
    return JSONResponse(
        content=dict(event=event, wf_status=str(status), workflow_id=handle.workflow_id)
    )


@DBOS.transaction()
def get_transaction_errors():
    # errors = DBOS.sql_session.query(Errors).all()
    errors = DBOS.sql_session.execute(
        select(Errors.id, Errors.message).order_by(Errors.created_at.desc())
    ).all()
    return {str(e.id): e.message for e in errors}


@DBOS.workflow()
def get_worflow_errors():
    return get_transaction_errors()


@app.get(
    "/errors", summary="Get all errors", description="Get all errors from the database"
)
def get_errors():
    DBOS.span.set_attribute("endpoint", "errors")
    ret = get_worflow_errors()
    return JSONResponse(content=ret)


@app.post(
    "/batch/{count}",
    summary="Start a batch workflow",
    description="Start a batch workflow with a list of user ids",
)
def batch_endpoint(count: int):
    DBOS.span.set_attributes({"endpoint": "batch", "count": count})
    wfid = str(uuid.uuid4())

    user_ids = [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
    ]
    user_ids = user_ids * count

    with SetWorkflowID(wfid):
        handle: WorkflowHandle = DBOS.start_workflow(process_tasks, user_ids)

    status: WorkflowStatus = handle.get_status()
    event = DBOS.get_event(handle.workflow_id, EVENT_KEY)
    if not status:
        raise HTTPException(status_code=404, detail="batch workflow failed to start")
    return JSONResponse(
        content=dict(event=event, wf_status=str(status), workflow_id=handle.workflow_id)
    )
