import os
from time import sleep

from dbos import DBOS, DBOSConfig, WorkflowHandle
from dbos._error import DBOSMaxStepRetriesExceeded


@DBOS.step(retries_allowed=True)
def provision_step():
    DBOS.logger.info(
        f"Step: Starting provision_step {DBOS.step_status.current_attempt + 1} of {DBOS.step_status.max_attempts}"
    )
    # Simulate some work
    sleep(1)
    raise ValueError("Simulated failure in provision_step")


@DBOS.workflow()
def provision_workflow() -> bool:
    DBOS.logger.info("Workflow: Starting")

    try:
        # This works
        provision_step()
    except DBOSMaxStepRetriesExceeded:
        DBOS.logger.error("Workflow: Caught max retries exceeded exception")

    DBOS.logger.info("Workflow: Finishing")
    return True


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
    handle: WorkflowHandle = DBOS.start_workflow(provision_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    DBOS.logger.info(f"Main: Workflow output: {output}")
