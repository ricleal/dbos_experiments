"""
This might be wrong as I call a workflow from a workflow. 
Also I can't call transactions from a step, thus the 2nd workflow.
"""

import json
import os
import uuid
from typing import Dict, List

import requests
from dbos import DBOS, Queue
from opentelemetry import trace
from sqlalchemy import insert

from exp.models import Errors, RandomUsers

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
        # DBOS.logger.info("Using local data")
        with open(local_data, "r") as f:
            return json.load(f)
    # DBOS.logger.info("Getting data from remote")
    response = requests.get(URL)
    data = response.json()
    with open(local_data, "w") as f:
        json.dump(data, f)
    return data


@DBOS.transaction()
def insert_user(users: List[Dict]):
    result = DBOS.sql_session.execute(insert(RandomUsers).values(users))
    # DBOS.logger.info(f"Workflow step transaction: {result.rowcount} rows inserted")
    # DBOS.span.add_event("insert_user", {"users": len(users)})


@DBOS.transaction()
def insert_error(error: str):
    # DBOS.span.set_attribute("error", error)
    result = DBOS.sql_session.execute(
        insert(Errors).values(id=DBOS.workflow_id, message=str(error))
    )
    # DBOS.logger.error(f"Workflow error transaction: {result.rowcount} rows inserted")


@DBOS.workflow()
def process_chunk(chunk):
    DBOS.logger.info(f"Processing chunk: users_count={len(chunk)}")
    # DBOS.span.add_event("process_chunk", {"chunk_size": len(chunk)})

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
            DBOS.logger.info(f"Enqueuing {len(l)} users")
            handle = queue.enqueue(insert_user, l)
            # DBOS.logger.info(f"Enqueued {len(l)} users")
            task_handles.append(handle)
            l = []


@DBOS.workflow()
def process():
    DBOS.logger.info(f"Starting Workflow: workflow_id={DBOS.workflow_id}")

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_span_child") as process_span:
        process_span.set_attribute("workflow_id", DBOS.workflow_id)

        data = get_data()
        for i in range(0, len(data["results"]), 100):
            chunk = data["results"][i : i + 100]
            # DBOS.logger.info(f"Processing chunk {i} to {i+100}")
            process_chunk(chunk)

        for handle in task_handles:
            try:
                res = handle.get_result()
                # DBOS.logger.info(f"Task result: {res}")
            except Exception as e:
                DBOS.logger.error(f"Task failed: {handle}::{e}")
                DBOS.span.record_exception(e)
                insert_error(f"Task failed: {handle}::{e}")
                continue

    DBOS.logger.info(f"Finishing Workflow: workflow_id={DBOS.workflow_id}")


if __name__ == "__main__":
    DBOS.logger.info("Starting Main")
    process()
    DBOS.logger.info("Finished Main")
