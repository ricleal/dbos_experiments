import json
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Dict, List

from dbos import DBOS, Queue, WorkflowHandle, WorkflowStatus
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import insert, select, update
from sqlalchemy.engine.cursor import CursorResult

from .models import Accesses, AccessRequests, Errors, Users

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

app.mount(
    "/static", StaticFiles(directory="static"), name="static"
)  # Serve static files (like your HTML)
templates = Jinja2Templates(
    directory="templates"
)  # Serve your HTML using Jinja2 Templates

DBOS(fastapi=app)


EVENT_KEY = "event_key"


# it may not start more than 50 functions in 30 seconds
slack_queue = Queue("slack_queue", concurrency=10, limiter={"limit": 50, "period": 30})
mail_queue = Queue("mail_queue", concurrency=10, limiter={"limit": 50, "period": 30})
request_queue = Queue(
    "request_queue", concurrency=10, limiter={"limit": 50, "period": 30}
)

## Transactions


@DBOS.transaction()
def insert_access(access_id: str, user_id: str, status: Status = Status.requested):
    result: CursorResult = DBOS.sql_session.execute(
        insert(AccessRequests).values(
            access_id=access_id, user_id=user_id, status=status
        )
    )
    DBOS.logger.debug(
        dict(
            message="insert_access",
            access_id=access_id,
            user_id=user_id,
            status=status,
            rows=result.rowcount,
        )
    )


@DBOS.transaction()
def update_access(access_request_id: str, status: str):
    result: CursorResult = DBOS.sql_session.execute(
        update(AccessRequests)
        .where(AccessRequests.id == access_request_id)
        .values(status=status)
    )
    DBOS.logger.debug(
        dict(
            message="update_access",
            access_request_id=access_request_id,
            status=status,
            rows=result.rowcount,
        )
    )


@DBOS.transaction()
def get_accesses(user_id: str = None) -> List[Accesses]:
    if user_id:
        accesses = DBOS.sql_session.execute(
            select(AccessRequests, Accesses, Users)
            .join(Accesses)
            .join(Users)
            .where(AccessRequests.user_id == user_id)
            .order_by(AccessRequests.created_at.desc())
        ).fetchall()
    else:
        accesses = DBOS.sql_session.execute(
            select(AccessRequests, Accesses, Users)
            .join(Accesses)
            .join(Users)
            .order_by(AccessRequests.created_at.desc())
        ).fetchall()
    accesses_json = [
        {
            "access_request_id": str(access[0].id),
            "access_request_created_at": access[0].created_at.isoformat(),
            "access_request_status": access[0].status,
            "access_id": str(access[1].id),
            "access_description": access[1].description,
            "user_id": str(access[2].id),
            "user_name": access[2].name,
        }
        for access in accesses
    ]
    DBOS.logger.debug(dict(message="get_accesses", accesses=accesses_json))
    return accesses_json


@DBOS.transaction()
def insert_error(error: Dict[str, str]):
    result: CursorResult = DBOS.sql_session.execute(
        insert(Errors).values(message=error)
    )
    DBOS.logger.debug(dict(message="insert_error", error=error, rows=result.rowcount))


# Store connected websockets
connected_websockets: List[WebSocket] = []

## Auxiliary functions


async def send_data(websocket: WebSocket, data: List[Dict] | str):
    """Sends data to the websocket."""
    try:
        await websocket.send_text(json.dumps({"data": data}))
    except RuntimeError:  # This can happen if the client disconnects
        connected_websockets.remove(websocket)


@DBOS.step()
async def send_notification(message: str):
    """Sends a notification to all connected websockets."""
    for websocket in connected_websockets:
        try:
            await send_data(websocket, message)
        except RuntimeError:
            pass  # Handle disconnections gracefully


## Scheduled workflows


@DBOS.scheduled("0/5 * * * * *")  # crontab syntax to run once every 5 seconds
@DBOS.workflow()
async def example_scheduled_workflow(scheduled_time: datetime, actual_time: datetime):
    accesses = get_accesses()
    DBOS.logger.info(dict(message="Scheduled workflow", accesses=accesses))

    if len(connected_websockets) > 0:
        await send_data(connected_websockets[-1], accesses)
    else:
        DBOS.logger.warning("No connected websockets to send data to")


## Workflows
@DBOS.workflow()
def process_access_request(access_id: str, user_id: str):
    DBOS.logger.info("Access request processed")
    handles = [
        request_queue.enqueue(insert_access, access_id, user_id),
        slack_queue.enqueue(
            send_notification, f"Slack: New access request received for user {user_id}"
        ),
        mail_queue.enqueue(
            send_notification, f"Slack: New access request received for user {user_id}"
        ),
    ]
    for handle in handles:
        try:
            result = handle.get_result()
            DBOS.logger.info(
                dict(
                    message="Workflow step completed",
                    access_id=access_id,
                    user_id=user_id,
                    result=result,
                )
            )
        except Exception as e:
            d = dict(
                message="Workflow step failed",
                access_id=access_id,
                user_id=user_id,
            )

            insert_error(d | {"error": str(e)})
            DBOS.logger.exception(d)


@DBOS.workflow()
def process_approve_request(access_request_id: str, status: str):
    DBOS.logger.info("Access request approved")
    handles = [
        request_queue.enqueue(update_access, access_request_id, status),
        slack_queue.enqueue(
            send_notification,
            f"Slack: Access request {status} for request {access_request_id}",
        ),
        mail_queue.enqueue(
            send_notification,
            f"Email: Access request {status} for request {access_request_id}",
        ),
    ]
    for handle in handles:
        try:
            result = handle.get_result()
            DBOS.logger.info(
                dict(
                    message="Workflow step completed",
                    access_request_id=access_request_id,
                    result=result,
                )
            )
        except Exception as e:
            d = dict(
                message="Workflow step failed",
                access_request_id=access_request_id,
                status=status,
            )

            insert_error(d | {"error": str(e)})
            DBOS.logger.exception(d)


## API Endpoints


@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    """Handles websocket connections."""
    await websocket.accept()
    connected_websockets.append(websocket)  # Add the new websocket to the list

    try:
        data = get_accesses()
        await send_data(websocket, data)  # Send initial data
        while (
            True
        ):  # Keep the connection open for potential future messages (if needed)
            await websocket.receive_text()  # Or websocket.receive_json() if you expect JSON from the client
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        connected_websockets.remove(websocket)  # Remove the websocket when it closes


@app.post("/api/request/{user_id}/{access_id}")
async def request_access(user_id: str, access_id: str):
    """Handles access request."""
    handle: WorkflowHandle = DBOS.start_workflow(
        process_access_request, access_id, user_id
    )
    status: WorkflowStatus = handle.get_status()
    if not status:
        raise HTTPException(status_code=404, detail="workflow failed to start")
    return JSONResponse(
        content=dict(wf_status=str(status), workflow_id=handle.workflow_id)
    )


@app.post("/api/approve")
async def approve_request(request: Request):
    """Handles approval/rejection requests."""
    try:
        request_data = await request.json()
        # {"access_request_id":"00000000-0000-0000-0000-000000000001","status":"APPROVED"}
        access_request_id = request_data.get("access_request_id")
        status = request_data.get("status").lower()

        if not access_request_id or not status:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # update_access(access_request_id, status)
        handle: WorkflowHandle = DBOS.start_workflow(
            process_approve_request, access_request_id, status
        )
        status: WorkflowStatus = handle.get_status()
        return {
            "message": "Request processed successfully",
            "workflow_id": handle.workflow_id,
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )  # Render the HTML template
