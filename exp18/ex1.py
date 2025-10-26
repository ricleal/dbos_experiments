import asyncio
import logging
import os
import sys
import time

import httpx
from dbos import DBOS, DBOSConfig, WorkflowHandle
from rate_limiter import rate_limit

# Example of using the rate limiter in a step


@DBOS.step(retries_allowed=True)
async def call_api_step(url: str) -> str:
    """Fast mock API call for testing rate limiter without external throttling"""
    DBOS.logger.debug(
        f"\tStep: Mock API call {DBOS.step_status.current_attempt + 1} of {DBOS.step_status.max_attempts}"
    )
    # Simulate minimal work
    await asyncio.sleep(0.001)
    return f"mock_response_for_{url}"


@DBOS.step(retries_allowed=True)
async def call_real_api_step(url: str) -> str:
    """Real API call - may be throttled by external services"""
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


# Create a rate-limited wrapper for calling the step
_rate_limit_start_time = None
_last_step_entry_time = None


@rate_limit(calls=4, period=1)
async def rate_limited_call_api(url: str) -> str:
    """Rate-limited wrapper that controls cadence of step invocations"""
    global _rate_limit_start_time, _last_step_entry_time

    if _rate_limit_start_time is None:
        _rate_limit_start_time = time.monotonic()

    entry_time = time.monotonic()
    elapsed = entry_time - _rate_limit_start_time

    if _last_step_entry_time is not None:
        gap = entry_time - _last_step_entry_time
        DBOS.logger.info(f"Step entering at {elapsed:.3f}s (gap: {gap * 1000:.0f}ms)")
    else:
        DBOS.logger.info(f"Step entering at {elapsed:.3f}s")

    _last_step_entry_time = entry_time
    return await call_api_step(url)


@DBOS.workflow()
async def orchestration_workflow() -> int:
    DBOS.logger.info("Workflow: Starting")

    bytes_size = 0

    for i in range(1, 21):
        # Using mock calls to verify rate limiter without external throttling
        r = await rate_limited_call_api("test_url")
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
