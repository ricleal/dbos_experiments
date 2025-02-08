"""
Note that I call a workflow from a workflow. 
I can't call transactions from a step, thus the 2nd workflow.
"""

import json
import logging
import os
import time
import uuid
from typing import Dict, List

import requests
from dbos import DBOS, Queue
from models import Errors, RandomUsers
from opentelemetry import trace
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import insert

log_handler = logging.StreamHandler()
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.handlers = [log_handler]

DBOS()
DBOS.launch()

queue = Queue("integration_queue")

URL = "https://randomuser.me/api?results=5000"

this_folder = os.path.dirname(os.path.abspath(__file__))
local_data = os.path.join(this_folder, "data", "data.json")

# holds the task handles so we can wait for them to finish
task_handles = []


def get_data():
    if os.path.exists(local_data):
        DBOS.logger.debug(dict(message="Getting data from local", path=local_data))
        with open(local_data, "r") as f:
            return json.load(f)
    DBOS.logger.debug(dict(message="Getting data from remote", url=URL))
    response = requests.get(URL)
    data = response.json()
    with open(local_data, "w") as f:
        json.dump(data, f)
    return data


@DBOS.transaction()
def insert_user(users: List[Dict]):
    DBOS.sql_session.execute(insert(RandomUsers).values(users))


@DBOS.transaction()
def insert_error(error: Dict[str, str]):
    result = DBOS.sql_session.execute(
        insert(Errors).values(id=DBOS.workflow_id, message=error)
    )
    DBOS.logger.error(dict(message="Error inserted", id=result.inserted_primary_key))


@DBOS.workflow()
def process_chunk(chunk):
    DBOS.logger.info(
        dict(
            message="Processing chunk",
            chunk_size=len(chunk),
            workflow_id=DBOS.workflow_id,
        )
    )

    l = []
    for idx, user in enumerate(chunk):
        d = {
            "id": uuid.uuid4(),
            # "id": uuid.uuid5(uuid.NAMESPACE_DNS, str(user["id"])),
            "gender": user["gender"],
            "title": user["name"]["title"],
            "first_name": user["name"]["first"],
            "last_name": user["name"]["last"],
            "street_number": user["location"]["street"]["number"],
            "street_name": user["location"]["street"]["name"],
            "city": user["location"]["city"],
            "state": user["location"]["state"],
            "country": user["location"]["country"],
            "postcode": user["location"]["postcode"],
            "latitude": user["location"]["coordinates"]["latitude"],
            "longitude": user["location"]["coordinates"]["longitude"],
            "timezone_offset": user["location"]["timezone"]["offset"],
            "timezone_description": user["location"]["timezone"]["description"],
            "email": user["email"],
            "uuid": user["login"]["uuid"],
            "username": user["login"]["username"],
            "password": user["login"]["password"],
            "salt": user["login"]["salt"],
            "md5": user["login"]["md5"],
            "sha1": user["login"]["sha1"],
            "sha256": user["login"]["sha256"],
            "date_of_birth": user["dob"]["date"],
            "age": user["dob"]["age"],
            "registered_at": user["registered"]["date"],
            "phone": user["phone"],
            "cell": user["cell"],
            "id_name": user["id"]["name"],
            "id_value": user["id"]["value"],
            "picture_large": user["picture"]["large"],
            "picture_medium": user["picture"]["medium"],
            "picture_thumbnail": user["picture"]["thumbnail"],
            "nat": user["nat"],
        }
        l.append(d)
        if idx > 0 and idx % 10 == 0:
            # Enqueue each task so all tasks are processed concurrently.
            DBOS.logger.debug(
                dict(
                    message="Enqueuing",
                    sub_chunk_size=len(l),
                    workflow_id=DBOS.workflow_id,
                )
            )
            handle = queue.enqueue(insert_user, l)
            task_handles.append(handle)
            l = []


@DBOS.workflow()
def process():
    DBOS.logger.info(dict(message="Starting Workflow", workflow_id=DBOS.workflow_id))

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_span_child") as process_span:
        process_span.set_attribute("workflow_id", DBOS.workflow_id)

        data = get_data()
        for i in range(0, len(data["results"]), 100):
            chunk = data["results"][i : i + 100]
            process_chunk(chunk)

        for handle in task_handles:
            try:
                res = handle.get_result()
            except Exception as e:
                m = dict(
                    message="Task failed",
                    wf_id=handle.get_workflow_id(),
                    status=handle.get_status().status,
                )
                DBOS.logger.exception(m)
                insert_error(m | {"error": str(e)})
                continue

    DBOS.logger.info(dict(message="Finished Workflow", workflow_id=DBOS.workflow_id))


if __name__ == "__main__":
    DBOS.logger.info(dict(message="Starting Main", timestamp=time.time()))
    process()
    DBOS.logger.info(dict(message="Finished Main", timestamp=time.time()))
