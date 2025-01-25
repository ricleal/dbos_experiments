import uuid
from enum import Enum

from dbos import DBOS, Queue, SetWorkflowID, WorkflowHandle, WorkflowStatus
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import insert
from sqlalchemy.engine.cursor import CursorResult

from exp.models import Accesses, Errors


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
    try:
        result: CursorResult = DBOS.sql_session.execute(
            insert(Accesses).values(user_id=task["user_id"], status=Status.requested)
        )
    except Exception as e:
        DBOS.sql_session.execute(insert(Errors).values(message=str(e)))
        # DBOS.logger.error(f"Error processing task: {str(e)}")
        return
    DBOS.logger.info(f"Workflow step transaction: {result.rowcount} rows inserted")


@DBOS.workflow()
def process_tasks(tasks: dict):
    DBOS.logger.info(f"I am a workflow with ID {DBOS.workflow_id}")
    DBOS.set_event(EVENT_KEY, DBOS.workflow_id)
    task_handles = []
    # Enqueue each task so all tasks are processed concurrently.
    for task in tasks:
        handle = queue.enqueue(process_task, dict(user_id=task))
        task_handles.append(handle)
    # Wait for each task to complete and retrieve its result.
    # Return the results of all tasks.
    # return [handle.get_result() for handle in task_handles]


@app.get("/")
def fastapi_endpoint():

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
