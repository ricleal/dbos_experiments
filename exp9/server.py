import os
import signal
import time
import uuid
from typing import Tuple

from dbos import DBOS, DBOSConfig, Queue, _utils

# Initialize DBOS with a unique executor ID
_utils.GlobalParams.executor_id = str(uuid.uuid4())

config: DBOSConfig = {
    "name": "fibonacci-server",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


Queue("my_queue", worker_concurrency=1)


def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@DBOS.step()
def calculate_fibonacci_step(n: int) -> Tuple[int, int, float]:
    """Step that calculates fibonacci number and measures duration"""
    DBOS.logger.info(
        dict(
            message="Starting fibonacci calculation",
            n=n,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    start_time = time.time()
    result = fibonacci(n)
    duration = time.time() - start_time

    DBOS.logger.info(
        dict(
            message="Fibonacci calculation completed",
            n=n,
            result=result,
            duration=duration,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    return n, result, duration


@DBOS.workflow()
def fibonacci_workflow(n: int) -> Tuple[int, int, float]:
    """Workflow that calculates fibonacci number"""
    DBOS.logger.info(
        dict(
            message="Fibonacci Workflow Started",
            wf_id=DBOS.workflow_id,
            n=n,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    result = calculate_fibonacci_step(n)

    DBOS.logger.info(
        dict(
            message="Fibonacci Workflow Completed",
            wf_id=DBOS.workflow_id,
            n=result[0],
            result=result[1],
            duration=result[2],
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    return result


if __name__ == "__main__":
    DBOS.logger.info(
        dict(
            message="Starting Fibonacci Server",
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        DBOS.logger.info(
            dict(
                message="Received signal, shutting down gracefully",
                signal=signum,
                pid=os.getpid(),
            )
        )
        DBOS.destroy()
        exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    DBOS.launch()

    # Keep the server running
    import threading

    threading.Event().wait()
