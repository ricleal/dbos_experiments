import os
import time

from dbos import DBOS, DBOSConfig, WorkflowHandle

# Example of measure payload size in a workflow
# A step is called with a payload of increasing size (10^0 to 10^6 bytes)
# we test a step which batches all payloads in a single call versus
# a step which is called multiple times with smaller payloads
# to see the performance difference.
#

MAX_SIZE = 7  # Up to 10^7 bytes (10 MB)


@DBOS.step(retries_allowed=True)
def size_step(payload_size: int) -> bytes:
    """A step that returns a payload of size 10^payload_size bytes."""
    payload = os.urandom(10**payload_size)  # Generate random bytes of size 10^i
    DBOS.logger.info(f"Step: Size step with payload size {len(payload)} bytes")
    return payload


@DBOS.workflow()
def size_workflow() -> bool:
    DBOS.logger.info("Workflow: Starting")

    times = []

    for i in range(MAX_SIZE):
        DBOS.logger.info(f"Workflow: Iteration {i + 1}/{MAX_SIZE}")

        start_time = time.time()
        payload = size_step(payload_size=i)
        times.append(time.time() - start_time)
        DBOS.logger.info(
            f"Workflow: Payload size is {len(payload)} bytes, took {times[-1] * 1000:.2f} ms"
        )
        if len(payload) != 10**i:
            raise ValueError(
                f"Payload size mismatch: expected {10**i}, got {len(payload)}"
            )
    total_time = sum(times)
    DBOS.logger.info(f"Workflow: Completed successfully in {total_time * 1000:.2f} ms")
    return True


@DBOS.step(retries_allowed=True)
def batch_size_step(iterations: int) -> bytes:
    payloads = []
    for i in range(iterations):
        payload = os.urandom(10**i)  # Generate random bytes of size 10^i
        DBOS.logger.info(f"Step: Batch size step iteration {i + 1}/{iterations}")
        payloads.append(payload)
    return b"".join(payloads)


@DBOS.workflow()
def batch_size_workflow() -> bool:
    DBOS.logger.info("Workflow: Starting")

    start_time = time.time()
    payload = batch_size_step(iterations=MAX_SIZE)
    DBOS.logger.info(
        f"Workflow: Payload size is {len(payload)} bytes, took {(time.time() - start_time) * 1000:.2f} ms"
    )

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
    handle: WorkflowHandle = DBOS.start_workflow(size_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    #
    # 2nd workflow
    DBOS.logger.info("----------------------------------------------------")
    handle = DBOS.start_workflow(batch_size_workflow)
    output = handle.get_result()
    DBOS.logger.info(f"Main: Workflow output: {output}")
