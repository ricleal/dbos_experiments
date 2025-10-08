import os
import random
import time
from datetime import datetime, timezone
from typing import List

from data import User, get_fake_users
from db import (
    create_database,
    get_most_recent_user_count,
    get_user_count,
    insert_users_page,
)
from dbos import DBOS, DBOSConfig, WorkflowHandle

# This represents a workflow and a step that might fail intermittently
# - When a step it is retried: max_attempts: int = 3,
# - When a workflow is retried, if any of steps were successful, their result is stored and reused.
#
# The workflow step simulates an API call and only generates users, and the insertion in the DB is done in the workflow
# Not in the step, so that if the step is retried, the users are not re-inserted.
# The analyzed_at date is different for each retry of the workflow, although the workflow_id is the same.
# This means that the combination of (user.id, workflow_id, analyzed_at) is always unique,
# so no UNIQUE constraint violations will occur.

# Create the database and table if they don't exist
create_database(db_path="data.db", truncate=False)


@DBOS.step(retries_allowed=True)
def users(page: int) -> List[User]:
    DBOS.logger.info("Step: Get simulated users from fake API")
    # let's simulate a failure 20% of the time
    if random.random() < 0.2:
        raise Exception("Simulated API failure")
    # End simulate
    user_list: List[User] = get_fake_users(seed=page, size=10)
    DBOS.logger.info("Step: Users generated successfully")
    return user_list


@DBOS.workflow(max_recovery_attempts=3)
def users_workflow() -> int:
    analyzed_at = datetime.now(timezone.utc)

    DBOS.logger.info(
        f"Workflow: Starting workflow with id: {DBOS.workflow_id} and analyzed_at: {analyzed_at.isoformat()}"
    )

    # Lets iterate through 10 pages of users
    # and insert them into the database
    # Simulate a failure 50% of the time during the workflow
    # to demonstrate DBOS's ability to recover
    for page in range(1, 11):
        DBOS.logger.info(f"Workflow: Processing page {page}")
        user_list: List[User] = users(page=page)
        insert_users_page(
            user_list=user_list, workflow_id=DBOS.workflow_id, analyzed_at=analyzed_at
        )
        # Simulate a OOM error
        if random.random() < 0.1:
            import ctypes

            ctypes.string_at(0)
        # End simulate

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

    # Get and log the current app version
    DBOS.logger.info(f"Current app version: {DBOS.application_version}")

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
    DBOS.logger.info(f"Main: Workflow output: {output} users processed")

    DBOS.logger.info(f"Main: Total most recent users: {get_most_recent_user_count()}")

    DBOS.logger.info("Main: Finishing")
