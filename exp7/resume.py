"""
Note that I call a workflow from a workflow.
I can't call transactions from a step, thus the 2nd workflow.
"""

import logging
import sys
import time
from collections import defaultdict

import dbos
from dbos import DBOS, Queue
from pythonjsonlogger.json import JsonFormatter

DBOS()

logger = logging.getLogger()
logger.handlers = []
# DBOS.logger.handlers = []

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
# DBOS.logger.addHandler(log_handler)
# Set the log level for the root logger
logger.setLevel(logging.INFO)


DBOS.launch()

queue = Queue("publisher_queue")
task_handles = []

global_published_messages = defaultdict(int)


@dbos.DBOS.dbos_class()
class Publisher(dbos.DBOSConfiguredInstance):
    def __init__(
        self,
        name: str,
    ):
        self.name = name
        # We need to keep a counter of published messages per workflow.
        self.local_published_messages = defaultdict(int)

        super().__init__(self.name)

    @dbos.DBOS.step()
    def publish(self, data, id, global_dic=global_published_messages):
        # publish the message
        global global_published_messages

        logger.info(
            dict(
                message="Publishing",
                data=data,
                local_count=self.local_published_messages[id],
                global_count=global_published_messages[id],
                publisher_name=self.name,
                workflow_id=id,
            )
        )

        self.local_published_messages[id] += 1

        global_published_messages[id] += 1
        time.sleep(0.1)

        # simulate a failure
        # if random.random() < 0.1:
        #     # simulate a failure
        #     logger.error(dict(message="Simulating failure"))
        #     os.kill(os.getpid(), signal.SIGTERM)


@DBOS.workflow()
def process():

    n_messages = 20

    p = Publisher(name="publisher1")
    for i in range(n_messages):

        data = {"message": f"Message {i}"}

        handle = queue.enqueue(
            p.publish, data=data, id=["workflow1", "workflow2"][i % 2]
        )
        task_handles.append(handle)

    for handle in task_handles:
        try:
            res = handle.get_result()
            logger.info(
                dict(
                    message="Task completed",
                    result=res,
                )
            )
        except Exception as e:
            logger.error(
                dict(
                    message="Error in task",
                    task_id=handle.task_id,
                    error=str(e),
                )
            )


if __name__ == "__main__":
    process()
