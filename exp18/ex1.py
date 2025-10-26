import logging
import os
import sys
import time

import httpx
from dbos import DBOS, DBOSConfig, WorkflowHandle
from rate_limiter import rate_limit

# Example of using the rate limiter in a step


@rate_limit(calls=4, period=1)
@DBOS.step(retries_allowed=True)
async def call_api_step(url: str) -> str:
    DBOS.logger.debug(
        f"\tStep: Starting calling API {DBOS.step_status.current_attempt + 1} of {DBOS.step_status.max_attempts} :: {url}"
    )
    async with httpx.AsyncClient() as client:
        call_duration_start = time.monotonic()
        response = await client.get(url)
        call_duration_end = time.monotonic()
        DBOS.logger.info(
            f"\tStep: HTTP call duration: {(call_duration_end - call_duration_start) * 1000:.0f}ms"
        )
        response.raise_for_status()
    r = response.text
    return r


@DBOS.workflow()
async def orchestration_workflow() -> int:
    DBOS.logger.info("Workflow: Starting")

    bytes_size = 0
    start = time.time()
    last_call_time = None

    for i in range(1, 21):
        elapsed = time.time() - start

        # Log time between calls
        if last_call_time is not None:
            time_since_last = elapsed - last_call_time
            DBOS.logger.info(
                f"Call {i} at {elapsed:.3f}s (gap: {time_since_last * 1000:.0f}ms)"
            )
        else:
            DBOS.logger.info(f"Call {i} at {elapsed:.3f}s")

        call_start = time.time()
        r = await call_api_step("https://www.cloudflare.com/cdn-cgi/trace")
        call_end = time.time()

        DBOS.logger.info(f"\tStep completed in {(call_end - call_start) * 1000:.0f}ms")
        last_call_time = elapsed
        bytes_size += sys.getsizeof(r)

    DBOS.logger.info("Workflow: Finishing")
    return bytes_size


if __name__ == "__main__":
    config: DBOSConfig = {
        "name": "dbos-starter",
        "database_url": os.getenv(
            "DBOS_DATABASE_URL",
            "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        ),
        "log_level": "INFO",
    }
    DBOS(config=config)
    DBOS.launch()

    # Configure milliseconds in logs and suppress verbose libraries
    for h in logging.root.handlers + logging.getLogger("dbos").handlers:
        h.setFormatter(
            logging.Formatter(
                # "%(asctime)s.%(msecs)03d [%(levelname)8s] (%(name)s:%(filename)s:%(lineno)d) %(message)s",
                "%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s",
                "%H:%M:%S",
            )
        )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Start the background task
    handle: WorkflowHandle = DBOS.start_workflow(orchestration_workflow)
    # Wait for the background task to complete and retrieve its result.
    output = handle.get_result()
    DBOS.logger.info(f"Main: Workflow output: {output}")
