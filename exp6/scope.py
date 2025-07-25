import datetime
import logging
import sys
import time

from dbos import DBOS
from pythonjsonlogger.json import JsonFormatter

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.addHandler(log_handler)
DBOS()


logger = logging.getLogger("exp6")
logger.setLevel(DBOS.logger.level)
logger.addHandler(log_handler)

DBOS.launch()

app_name = "exp6-scope"


@DBOS.dbos_class()
class A:

    counter = 0

    def __init__(self, instance_id: str):
        self.instance_id = instance_id

    @DBOS.step()
    def step(self, step_number: int = 0):
        global app_name
        logger.info(
            dict(
                message="instance step",
                instance_id=self.instance_id,
                app_name=app_name,
                step_number=step_number,
            )
        )
        self.counter += 1
        time.sleep(0.5)

    @staticmethod
    @DBOS.workflow()
    def workflow():
        global app_name

        logger.info(dict(message="Starting Workflow", app_name=app_name))

        a = A(datetime.datetime.now().isoformat())
        for i in range(30):
            a.step(i)

        logger.info(dict(message="Finished Workflow", app_name=app_name))


if __name__ == "__main__":
    logger.info(dict(message="Starting Main", app_name=app_name))
    A.workflow()
    logger.info(dict(message="Finished Main", app_name=app_name))
    DBOS.destroy()
    sys.exit(0)
