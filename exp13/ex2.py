import os
from datetime import datetime, timezone
from typing import List

from data import User, get_fake_users
from db import (
    create_database,
    get_user_count,
    insert_users_page,
)
from dbos import DBOS, DBOSConfig, WorkflowHandle

# This is all working

analyzed_at = datetime.now(timezone.utc)


@DBOS.step(retries_allowed=True)
def users(page: int, workflow_id: str, analyzed_at: datetime) -> bool:
    DBOS.logger.info("Step: Inserting users into the database")
    user_list: List[User] = get_fake_users(seed=page, size=10)

    print(f"Users: {[u.name for u in user_list]}")
    # Insert a batch of users
    insert_users_page(
        user_list=user_list,
        workflow_id=workflow_id,
        analyzed_at=analyzed_at,
    )

    # Simulate error after insert so this step can be retried
    # there will be an error on db: we trying to insert the same users again
    # sqlite3.IntegrityError: UNIQUE constraint failed: users.id, users.workflow_id, users.analyzed_at
    if (
        DBOS.step_status.current_attempt is not None
        and DBOS.step_status.max_attempts is not None
        and DBOS.step_status.current_attempt < DBOS.step_status.max_attempts - 1
    ):
        raise ValueError(
            f"Simulated error on attempt after insertion {DBOS.step_status.current_attempt}"
        )

    DBOS.logger.info("Step: Users inserted successfully")
    return True


@DBOS.workflow()
def users_workflow() -> int:
    DBOS.logger.info("Workflow: Starting")

    # Create the database and table if they don't exist
    create_database(db_path="data.db", truncate=True)

    results: List[bool] = []
    # Run the users step twice to demonstrate idempotency
    for r in range(2):
        DBOS.logger.info(f"Workflow: Running users step, iteration {r + 1}")
        result: bool = users(
            page=r, workflow_id=DBOS.workflow_id, analyzed_at=analyzed_at
        )
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
    # Start the background task
    handle: WorkflowHandle = DBOS.start_workflow(users_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    DBOS.logger.info(f"Main: Workflow output: {output}")
