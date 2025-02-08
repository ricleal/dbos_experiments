# Description: This is a simple example of how to use the python-json-logger library to log messages in JSON format.
# `poetry add python-json-logger`
import logging
import sys
from time import sleep

from dbos import DBOS, WorkflowHandle
from pythonjsonlogger.json import JsonFormatter

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.handlers = [log_handler]


DBOS()
DBOS.launch()


DBOS.logger.info(dict(message="start"))


@DBOS.workflow(max_recovery_attempts=1)
def my_workflow(step: int):
    DBOS.logger.info(dict(message="workflow"))
    for step in range(step):
        DBOS.sleep(1)
        DBOS.logger.info(dict(message="step", step=step, id=DBOS.workflow_id))
    return dict(message="FINISHED", step=step, id=DBOS.workflow_id)


DBOS.logger.info(dict(message="workflow started asynch"))
handle: WorkflowHandle = DBOS.start_workflow(my_workflow, 5)
workflow_id = handle.get_workflow_id()
status = handle.get_status()
DBOS.logger.info(
    dict(message="workflow started", workflow_id=workflow_id, status=status)
)

DBOS.logger.info(dict(message="doing other stuff"))
sleep(2)
status = handle.get_status()
DBOS.logger.info(dict(message="waiting for workflow to finish", status=status))
result = handle.get_result()

DBOS.logger.info(dict(message="workflow finished", result=result))


DBOS.logger.info(dict(message="end"))
