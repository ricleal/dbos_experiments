import os

from dbos import DBOS, DBOSConfig, WorkflowHandle
from sqlalchemy import text


@DBOS.transaction()
def my_transaction():
    result = DBOS.sql_session.execute(text("SELECT current_database(), current_user;"))
    return result.fetchone()


@DBOS.step()
def my_step():
    DBOS.logger.info("Executing my_step")
    try:
        # This will throw an error, because transactions cannot be called from steps
        r = my_transaction()
    except Exception as e:
        DBOS.logger.error(f"Error occurred in my_step: {e}")
        return
    DBOS.logger.info(f"my_transaction() returned: {r}")


@DBOS.workflow()
def my_sub_workflow():
    DBOS.logger.info("Starting my_sub_workflow")
    r = my_transaction()
    DBOS.logger.info(f"my_transaction() returned: {r}")
    DBOS.logger.info("Finishing my_sub_workflow")
    ##  Apparently we have access to DBOS.sql_session
    DBOS.sleep(2)
    # result = DBOS.sql_session.execute(text("SELECT current_database(), current_user;"))
    # DBOS.logger.info(f"DBOS.sql_session returned: {result.fetchone()}")


@DBOS.workflow()
def my_workflow():
    DBOS.logger.info("Starting my_workflow")
    # my_step()
    my_sub_workflow()
    DBOS.logger.info("Finishing my_workflow")


if __name__ == "__main__":
    config: DBOSConfig = {
        "name": "dbos-starter",
        "database_url": os.getenv(
            "DBOS_DATABASE_URL",
            "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        ),
    }
    DBOS(config=config, conductor_key="supersecret")
    DBOS.launch()
    # Start the background task
    handle: WorkflowHandle = DBOS.start_workflow(my_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
