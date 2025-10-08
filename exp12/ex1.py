import os
from typing import List

from dbos import DBOS, DBOSConfig, WorkflowHandle

# EXample with tests in test_ex1.py


@DBOS.step(retries_allowed=True)
def success_step() -> bool:
    DBOS.logger.info("Executing success_step")
    return True


@DBOS.step(retries_allowed=True)
def failure_step() -> bool:
    DBOS.logger.info("Executing failure_step")
    raise ValueError("Simulated failure in failure_step")


@DBOS.workflow()
def my_workflow() -> List[bool]:
    DBOS.logger.info("Starting my_workflow")
    r1 = success_step()
    r2 = failure_step()
    DBOS.logger.info("Finishing my_workflow")
    return [r1, r2]


if __name__ == "__main__":
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
    handle: WorkflowHandle = DBOS.start_workflow(my_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    print("Workflow output:", output)
