# Description: This is a simple example of how to use the python-json-logger library to log messages in JSON format.
# `poetry add python-json-logger`
import logging
import sys

from dbos import DBOS
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


DBOS.logger.info(
    {
        "my_data": 1,
        "message": "this is a message",
        "other_stuff": False,
        "nested": {"a": 1, "b": 2},
    }
)

DBOS.logger.info(dict(message="this is a message", other_stuff=True))
