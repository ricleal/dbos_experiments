import logging
import sys

from dbos import DBOS, Queue, WorkflowHandle
from pythonjsonlogger.json import JsonFormatter

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(process)d %(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.addHandler(log_handler)
DBOS()


logger = logging.getLogger("exp6")
logger.setLevel(DBOS.logger.level)
logger.addHandler(log_handler)


DBOS.launch()

queue = Queue("example_queue")


@DBOS.step()
def wf_step():
    logger.info(
        dict(
            message="Step Started",
            parent_wf_id=DBOS.parent_workflow_id,
            wf_id=DBOS.workflow_id,
        )
    )


@DBOS.workflow()
def wf_child(queued=False):
    logger.info(
        dict(
            message="Child Workflow Started",
            parent_wf_id=DBOS.parent_workflow_id,
            wf_id=DBOS.workflow_id,
            queued=queued,
        )
    )
    DBOS.sleep(1)
    if queued:
        h = queue.enqueue(wf_step)
        h.get_result()
    else:
        wf_step()


@DBOS.workflow()
def wf(queued=False):
    logger.info(
        dict(
            message="Workflow Started",
            parent_wf_id=DBOS.parent_workflow_id,
            wf_id=DBOS.workflow_id,
            queued=queued,
        )
    )
    DBOS.sleep(1)
    if queue:
        h = queue.enqueue(wf_child, True)
        h.get_result()
    else:
        wf_child()


@DBOS.workflow()
def wf_root(queued=False):
    logger.info(
        dict(
            message="Root Workflow Started",
            parent_wf_id=DBOS.parent_workflow_id,
            wf_id=DBOS.workflow_id,
            queued=queued,
        )
    )
    DBOS.sleep(1)
    if queued:
        h = queue.enqueue(wf, True)
        h.get_result()
    else:
        wf()


if __name__ == "__main__":
    logger.info(dict(message="Starting Main"))
    wf_root()
    logger.info(dict(message="Launching asynch workflow"))
    handle: WorkflowHandle = DBOS.start_workflow(wf_root, True)
    handle.get_result()  # wait for the workflow to finish
    logger.info(dict(message="Finished Main"))
    DBOS.destroy()
    sys.exit(0)
