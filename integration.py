import json
import os
import uuid
from typing import Dict, List

import requests
from dbos import DBOS, Queue
from sqlalchemy import insert

from exp.models import RandomUsers

DBOS()
DBOS.launch()

queue = Queue("integration_queue")

URL = "https://randomuser.me/api?results=1000"

this_folder = os.path.dirname(os.path.abspath(__file__))
local_data = os.path.join(this_folder, "data", "data.json")

# holds the task handles so we can wait for them to finish
task_handles = []


def get_data():
    if os.path.exists(local_data):
        with open(local_data, "r") as f:
            return json.load(f)
    response = requests.get(URL)
    data = response.json()
    with open(local_data, "w") as f:
        json.dump(data, f)
    return data


@DBOS.transaction()
def insert_user(users: List[Dict]):
    result = DBOS.sql_session.execute(insert(RandomUsers).values(users))
    DBOS.logger.info(f"Workflow step transaction: {result.rowcount} rows inserted")


@DBOS.workflow()
def process_chunk(chunk):
    DBOS.logger.info(f"Processing chunk of {len(chunk)} users")
    l = []
    for idx, user in enumerate(chunk):
        d = {
            "id": uuid.uuid5(uuid.NAMESPACE_DNS, str(user["id"])),
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
            DBOS.logger.info(f"Enqueued {len(l)} users")
            task_handles.append(handle)
            l = []


@DBOS.workflow()
def process():
    DBOS.logger.info(f"Starting Workflow ID {DBOS.workflow_id}")

    data = get_data()
    for i in range(0, len(data["results"]), 100):
        chunk = data["results"][i : i + 100]
        DBOS.logger.info(f"Processing chunk {i} to {i+100}")
        process_chunk(chunk)

    for handle in task_handles:
        try:
            res = handle.get_result()
            DBOS.logger.info(f"Task result: {res}")
        except Exception as e:
            DBOS.logger.error(f"Task failed: {handle}::{e}")
            continue

    DBOS.logger.info(f"Finishing Workflow ID {DBOS.workflow_id}")


if __name__ == "__main__":
    DBOS.logger.info("Starting Main")
    process()
    DBOS.logger.info("Finished Main")
