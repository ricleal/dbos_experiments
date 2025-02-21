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

app_name = "exp6"


@DBOS.dbos_class()
class A:

    counter = 0

    def __init__(self, instance_id: str):
        self.instance_id = instance_id

    @DBOS.step()
    def step(self):
        self.instance_id = f"{self.instance_id}_{self.counter}"
        logger.info(
            dict(message="step", instance_id=self.instance_id, app_name=app_name)
        )
        self.counter += 1

    @staticmethod
    @DBOS.workflow()
    def workflow():

        a = A("a")
        a.step()
        a.step()


if __name__ == "__main__":
    logger.info(dict(message="Starting Main", timestamp=time.time(), app_name=app_name))
    A.workflow()
    logger.info(dict(message="Finished Main", timestamp=time.time(), app_name=app_name))
    DBOS.destroy()
    sys.exit(0)
