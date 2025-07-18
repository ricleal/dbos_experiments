import logging
import os
import time
from multiprocessing import Pool
from typing import Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def parallel_workflow(p: int) -> Tuple[int, int]:
    # print pid
    logger.info(
        dict(
            message="Parallel Workflow Started",
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )
    t = time.time()
    res = fibonacci(p)  # Simulating some work
    t = time.time() - t
    logger.info(
        dict(
            message="Parallel Workflow Completed",
            pid=os.getpid(),
            ppid=os.getppid(),
            duration=t,
        )
    )
    return p, res


if __name__ == "__main__":
    logger.info(
        dict(
            message="Starting Parallel Workflows",
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    with Pool(10) as p:
        results = p.map(parallel_workflow, list(range(30, 50)))
    for p, res in results:
        logger.info(
            dict(
                message="Parallel Workflow Result",
                p=p,
                result=res,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )

# ❯ python exp8/exp_multip.py
# INFO:__main__:{'message': 'Starting Parallel Workflows', 'pid': 815969, 'ppid': 796045}
# INFO:__main__:{'message': 'Parallel Workflow Started', 'pid': 815975, 'ppid': 815969}
# INFO:__main__:{'message': 'Parallel Workflow Started', 'pid': 815976, 'ppid': 815969}
# INFO:__main__:{'message': 'Parallel Workflow Started', 'pid': 815977, 'ppid': 815969}
# INFO:__main__:{'message': 'Parallel Workflow Started', 'pid': 815978, 'ppid': 815969}
# INFO:__main__:{'message': 'Parallel Workflow Started', 'pid': 815979, 'ppid': 815969}
# INFO:__main__:{'message': 'Parallel Workflow Completed', 'pid': 815975, 'ppid': 815969, 'duration': 0.21837687492370605}
# INFO:__main__:{'message': 'Parallel Workflow Completed', 'pid': 815976, 'ppid': 815969, 'duration': 0.5323739051818848}
# INFO:__main__:{'message': 'Parallel Workflow Completed', 'pid': 815977, 'ppid': 815969, 'duration': 1.3656704425811768}
# INFO:__main__:{'message': 'Parallel Workflow Completed', 'pid': 815978, 'ppid': 815969, 'duration': 3.433776378631592}
# INFO:__main__:{'message': 'Parallel Workflow Completed', 'pid': 815979, 'ppid': 815969, 'duration': 8.709744215011597}
# INFO:__main__:{'message': 'Parallel Workflow Result', 'p': 30, 'result': 832040, 'pid': 815969, 'ppid': 796045}
# INFO:__main__:{'message': 'Parallel Workflow Result', 'p': 32, 'result': 2178309, 'pid': 815969, 'ppid': 796045}
# INFO:__main__:{'message': 'Parallel Workflow Result', 'p': 34, 'result': 5702887, 'pid': 815969, 'ppid': 796045}
# INFO:__main__:{'message': 'Parallel Workflow Result', 'p': 36, 'result': 14930352, 'pid': 815969, 'ppid': 796045}
# INFO:__main__:{'message': 'Parallel Workflow Result', 'p': 38, 'result': 39088169, 'pid': 815969, 'ppid': 796045}
