import os
import random
import time
from datetime import datetime, timezone
from typing import List

from data import User, get_fake_users
from db import (
    create_database,
    get_user_count,
    insert_users_page,
)
from dbos import DBOS, DBOSConfig, WorkflowHandle

# This represents a workflow that may fail intermittently
# and demonstrates DBOS's ability to recover from such failures.
# The data is inserted in the DB successfully.

analyzed_at = datetime.now(timezone.utc)

# random.seed(123)


@DBOS.step(retries_allowed=True)
def users(page: int, workflow_id: str, analyzed_at: datetime) -> bool:
    DBOS.logger.info("Step: Inserting users into the database")
    user_list: List[User] = get_fake_users(seed=page, size=10)

    # Insert a batch of users
    insert_users_page(
        user_list=user_list,
        workflow_id=workflow_id,
        analyzed_at=analyzed_at,
    )
    DBOS.logger.info("Step: Users inserted successfully")
    return True


@DBOS.workflow(max_recovery_attempts=3)
def users_workflow() -> int:
    DBOS.logger.info(f"Workflow: Starting workflow {DBOS.workflow_id}")

    # Create the database and table if they don't exist
    create_database(db_path="data.db", truncate=True)

    results: List[bool] = []

    result: bool = users(page=1, workflow_id=DBOS.workflow_id, analyzed_at=analyzed_at)
    results.append(result)

    # Simulate a OOM error
    if random.random() < 0.5:
        import ctypes

        ctypes.string_at(0)
    # End simulate

    result: bool = users(page=2, workflow_id=DBOS.workflow_id, analyzed_at=analyzed_at)
    results.append(result)

    user_count = get_user_count()
    DBOS.logger.info("Workflow: Finishing")
    return user_count


if __name__ == "__main__":
    DBOS.logger.info("Main: Starting")
    config: DBOSConfig = {
        "name": "dbos-starter",
        "database_url": os.getenv(
            "DBOS_DATABASE_URL",
            "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        ),
        "log_level": "DEBUG",
    }
    DBOS(config=config)
    DBOS.launch()

    # Check for pending workflows
    pending_workflows = DBOS.list_workflows(
        status=["PENDING", "ENQUEUED"], name="users_workflow"
    )

    if pending_workflows:
        DBOS.logger.info(
            f"Found {len(pending_workflows)} pending workflows. Waiting for them to complete..."
        )

        # Wait a few seconds to give DBOS time to execute pending workflows
        wait_time = 5  # seconds
        DBOS.logger.info(f"Waiting {wait_time} seconds...")
        time.sleep(wait_time)

        # Check again for pending workflows
        pending_workflows = DBOS.list_workflows(
            status=["PENDING", "ENQUEUED"], name="users_workflow"
        )

        if pending_workflows:
            DBOS.logger.info(
                f"Still found {len(pending_workflows)} pending workflows after waiting. Using existing workflow."
            )
            # Use the existing workflow
            existing_workflow_id = pending_workflows[0].workflow_id
            DBOS.logger.info(f"Resuming workflow ID: {existing_workflow_id}")
            handle = DBOS.retrieve_workflow(existing_workflow_id)
        else:
            DBOS.logger.info(
                "No more pending workflows after waiting. Starting new workflow."
            )
            # Start the background task
            handle: WorkflowHandle = DBOS.start_workflow(users_workflow)
    else:
        DBOS.logger.info("No pending workflows found. Starting new workflow.")
        # Start the background task
        handle: WorkflowHandle = DBOS.start_workflow(users_workflow)

    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    DBOS.logger.info(f"Main: Workflow output: {output}")
