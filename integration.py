"""
Example of the retry mechanism in DBOS
See the step transform_data, which raises an exception when the data is "task 50"
"""

import random
from typing import Any, Dict

from dbos import DBOS, Queue
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from sqlalchemy import insert

from exp.models import Errors, Tasks

DBOS()
DBOS.launch()

random.seed(42)

queue = Queue("integration_queue")


# Configure the OTLP exporter
otlp_exporter = OTLPMetricExporter(endpoint="http://localhost:4317/v1/metrics")

# Create a MeterProvider
meter_provider = MeterProvider(
    metric_readers=[
        PeriodicExportingMetricReader(
            otlp_exporter, export_interval_millis=1000, export_timeout_millis=5000
        ),
        PeriodicExportingMetricReader(ConsoleMetricExporter()),
    ]
)

# Use the meter provider
metrics.set_meter_provider(meter_provider)

# Get a meter instance
meter = metrics.get_meter(__name__)

# Create a counter metric
counter = meter.create_counter(
    name="persistent_counter",
    description="This is a counter to count database operations",
    unit="1",
)


@DBOS.transaction()
def insert_error(message: str):
    counter.add(1, attributes=dict(operation="insert_error"))
    return DBOS.sql_session.execute(insert(Errors).values(message=message))


@DBOS.transaction()
def insert_task(data: Dict[str, Any], title: str = None):
    counter.add(1, attributes=dict(operation="insert_task"))
    return DBOS.sql_session.execute(insert(Tasks).values(data=data, title=title))


@DBOS.step(retries_allowed=True, max_attempts=1)
def transform_data(data: Dict[str, str]) -> Dict[str, str]:
    DBOS.logger.debug(f"Transforming data: {data}")
    if data["data"] == "task 50":
        raise ValueError("task 50 is invalid")
    return {k: v.upper() for k, v in data.items()}


@DBOS.workflow(max_recovery_attempts=3)
def process():
    DBOS.logger.info(f"Starting Workflow: workflow_id={DBOS.workflow_id}")

    data_transformed = []
    for i in range(100):
        try:
            data = transform_data(dict(data=f"task {i+random.randint(1, 100)}"))
            data_transformed.append(data)
            DBOS.logger.info(f"Transformed data: {data}")
            DBOS.sleep(0.1)
        except Exception as e:
            DBOS.logger.error(f"Error transforming data: {e}")
            insert_error(str(e))
            continue

    DBOS.logger.info(f"Inserting {len(data_transformed)} tasks in the database")
    handlers = [queue.enqueue(insert_task, data) for data in data_transformed]

    DBOS.logger.info(f"Waiting for {len(handlers)} tasks to finish")
    for handler in handlers:
        try:
            res = handler.get_result()
            if list(res):
                DBOS.logger.warning(f"Task returned: {res}")
        except Exception as e:
            DBOS.logger.error(f"Error inserting task: {e}")
            insert_error(str(e))
            continue

    DBOS.logger.info(f"Finishing Workflow: workflow_id={DBOS.workflow_id}")


if __name__ == "__main__":
    DBOS.logger.info("Starting Main")
    process()
    DBOS.logger.info("Finished Main")
