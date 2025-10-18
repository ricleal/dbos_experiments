import cProfile
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


@DBOS.workflow(max_recovery_attempts=3)
def users_batch_workflow(
    batch_number: int, batch_size: int = 10, total_batches: int = 10
) -> List[User]:
    """Process a batch of users by retrieving multiple pages of users."""
    DBOS.logger.info(f"Workflow: Starting batch {batch_number} of size {batch_size}")
    user_list: List[User] = []
    for page in range(1, batch_size + 1):
        DBOS.logger.info(f"Workflow: Processing page {page} of batch {batch_number}")
        user_list += users(page=page + (batch_number - 1) * batch_size)
    DBOS.logger.info(
        f"Workflow: Finishing batch {batch_number}: Total users so far: {len(user_list)}"
    )
    return user_list


@DBOS.step(retries_allowed=True)
def users(page: int) -> List[User]:
    """Simulate retrieving a page of users from an API.
    This step may fail intermittently to simulate API failures.
    """

    DBOS.logger.info(f"Step: Get simulated API users of page {page}")
    # let's simulate a failure
    if random.random() < 0.1:
        raise Exception("Simulated API failure")
    # End simulate
    user_list: List[User] = get_fake_users(seed=page, size=10)
    DBOS.logger.info("Step: Users generated successfully")
    return user_list


@DBOS.workflow(max_recovery_attempts=3)
def users_workflow() -> int:
    """
    Main workflow to process users in batches and insert them into the database.
    This workflow processes 10 batches of users, each containing 10 pages of users.
    Each batch is processed by the users_batch_workflow, which may be retried up to
    3 times in case of failure.
    """
    analyzed_at = datetime.now(timezone.utc)

    DBOS.logger.info(
        f"Workflow: Starting workflow with id: {DBOS.workflow_id} and analyzed_at: {analyzed_at.isoformat()}"
    )

    # Lets iterate through 10 batches of users
    for batch_number in range(1, 11):
        DBOS.logger.info(f"Workflow: Processing batch {batch_number} of 10")
        user_list: List[User] = users_batch_workflow(batch_number=batch_number)
        insert_users_page(
            user_list=user_list,
            workflow_id=DBOS.workflow_id,
            analyzed_at=analyzed_at,
        )
        # Simulate a OOM error
        if random.random() < 0.02:
            import ctypes

            ctypes.string_at(0)
        # End simulate

    user_count = get_most_recent_user_count(workflow_id=DBOS.workflow_id)
    DBOS.logger.info("Workflow: Finishing")
    return user_count


def main(users_workflow):
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

    # Start profiling the entire workflow execution
    profiler = cProfile.Profile()
    profiler.enable()

    try:
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

        DBOS.logger.info(f"Main: Total users in database: {get_user_count()}")

    finally:
        # Stop profiling and save results
        profiler.disable()
        profiler.dump_stats("main_profile.prof")

    DBOS.logger.info("Main: Finishing")


if __name__ == "__main__":
    main(users_workflow)
