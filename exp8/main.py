import asyncio
import os
import random
import time
from typing import Tuple

from dbos import DBOS, DBOSConfig, Queue, WorkflowHandleAsync

"""Example of using DBOS to run parallel workflows.
DBOS does NOT create a process per workflow. Since python parallelism is limited by the GIL,
I was expecting a process per workflow, to use python multiprocessing to bypass the GIL."""

config: DBOSConfig = {
    "name": "dbos-starter",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
    "log_level": "DEBUG",
}
DBOS(config=config)


def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@DBOS.workflow()
def parallel_workflow() -> Tuple[int, int]:
    # print pid
    DBOS.logger.info(
        dict(
            message="Parallel Workflow Started",
            wf_id=DBOS.workflow_id,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )
    t = time.time()
    p = random.randint(30, 40)
    res = fibonacci(p)  # Simulating some work
    t = time.time() - t
    DBOS.logger.info(
        dict(
            message="Parallel Workflow Completed",
            wf_id=DBOS.workflow_id,
            pid=os.getpid(),
            ppid=os.getppid(),
            duration=t,
        )
    )
    return p, res, t


queue = Queue("my_queue", concurrency=10, worker_concurrency=5)


async def main():
    DBOS.launch()

    DBOS.logger.info(
        dict(
            message="Starting Parallel Workflows",
            queue_name=queue.name,
            concurrency=queue.concurrency,
            worker_concurrency=queue.worker_concurrency,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    task_handles = []
    for i in range(5):
        handle: WorkflowHandleAsync = await queue.enqueue_async(parallel_workflow)
        task_handles.append(handle)

    # Process results as they complete (similar to asyncio.gather)
    for coro in asyncio.as_completed([handle.get_result() for handle in task_handles]):
        p, res, t = await coro
        DBOS.logger.info(
            dict(
                message="Parallel Workflow Result (as completed)",
                p=p,
                result=res,
                duration=t,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )


if __name__ == "__main__":
    asyncio.run(main())

# ❯ python exp8/main.py
# DBOS system database URL: postgresql://trustle:***@localhost:5432/test_dbos_sys?sslmode=disable
# DBOS application database URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
# Database engine parameters: {'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True, 'connect_args': {'connect_timeout': 10}}
# 18:56:22 [    INFO] (dbos:_dbos.py:370) Initializing DBOS (v2.1.0)
# 18:56:22 [    INFO] (dbos:_dbos.py:445) Executor ID: local_executer
# 18:56:22 [    INFO] (dbos:_dbos.py:446) Application version: local_v0
# 18:56:22 [ WARNING] (dbos:_dbos.py:486) Failed to start admin server: [Errno 98] Address already in use
# 18:56:22 [    INFO] (dbos:_dbos.py:496) No workflows to recover from application version local_v0
# 18:56:22 [    INFO] (dbos:_dbos.py:548) DBOS launched!
# To view and manage workflows, connect to DBOS Conductor at:https://console.dbos.dev/self-host?appname=dbos-starter
# 18:56:22 [    INFO] (dbos:main.py:59) {'message': 'Starting Parallel Workflows', 'queue_name': 'my_queue', 'concurrency': 10, 'worker_concurrency': 5, 'pid': 2895907, 'ppid': 1537078}
# 18:56:23 [   DEBUG] (dbos:_sys_db.py:1821) [my_queue] dequeueing 5 task(s)
# 18:56:24 [    INFO] (dbos:main.py:29) {'message': 'Parallel Workflow Started', 'wf_id': 'b11ec5d2-91f7-4f8b-929f-cb8b78814fbe', 'pid': 2895907, 'ppid': 1537078}
# 18:56:24 [    INFO] (dbos:main.py:29) {'message': 'Parallel Workflow Started', 'wf_id': '1fb2b7f0-148d-48ca-ac1a-ae66875bcc57', 'pid': 2895907, 'ppid': 1537078}
# 18:56:24 [    INFO] (dbos:main.py:29) {'message': 'Parallel Workflow Started', 'wf_id': '85bd3b22-d1ff-40a1-aca6-c95d99cffb95', 'pid': 2895907, 'ppid': 1537078}
# 18:56:24 [    INFO] (dbos:main.py:29) {'message': 'Parallel Workflow Started', 'wf_id': 'a122d739-2712-493e-ac5f-93f89ea9b33e', 'pid': 2895907, 'ppid': 1537078}
# 18:56:25 [    INFO] (dbos:main.py:29) {'message': 'Parallel Workflow Started', 'wf_id': '2e0efdea-179d-4f7e-867c-dbd7479e04a7', 'pid': 2895907, 'ppid': 1537078}
# 18:56:27 [    INFO] (dbos:main.py:41) {'message': 'Parallel Workflow Completed', 'wf_id': '2e0efdea-179d-4f7e-867c-dbd7479e04a7', 'pid': 2895907, 'ppid': 1537078, 'duration': 2.4000532627105713}
# 18:56:28 [    INFO] (dbos:main.py:41) {'message': 'Parallel Workflow Completed', 'wf_id': '1fb2b7f0-148d-48ca-ac1a-ae66875bcc57', 'pid': 2895907, 'ppid': 1537078, 'duration': 3.913741111755371}
# 18:56:29 [    INFO] (dbos:main.py:80) {'message': 'Parallel Workflow Result (as completed)', 'p': 30, 'result': 832040, 'duration': 2.4000532627105713, 'pid': 2895907, 'ppid': 1537078}
# 18:56:29 [    INFO] (dbos:main.py:80) {'message': 'Parallel Workflow Result (as completed)', 'p': 32, 'result': 2178309, 'duration': 3.913741111755371, 'pid': 2895907, 'ppid': 1537078}
# 18:56:31 [    INFO] (dbos:main.py:41) {'message': 'Parallel Workflow Completed', 'wf_id': '85bd3b22-d1ff-40a1-aca6-c95d99cffb95', 'pid': 2895907, 'ppid': 1537078, 'duration': 6.738726615905762}
# 18:56:31 [    INFO] (dbos:main.py:80) {'message': 'Parallel Workflow Result (as completed)', 'p': 33, 'result': 3524578, 'duration': 6.738726615905762, 'pid': 2895907, 'ppid': 1537078}
# 18:56:32 [    INFO] (dbos:main.py:41) {'message': 'Parallel Workflow Completed', 'wf_id': 'b11ec5d2-91f7-4f8b-929f-cb8b78814fbe', 'pid': 2895907, 'ppid': 1537078, 'duration': 8.584540605545044}
# 18:56:32 [    INFO] (dbos:main.py:41) {'message': 'Parallel Workflow Completed', 'wf_id': 'a122d739-2712-493e-ac5f-93f89ea9b33e', 'pid': 2895907, 'ppid': 1537078, 'duration': 7.941507816314697}
# 18:56:33 [    INFO] (dbos:main.py:80) {'message': 'Parallel Workflow Result (as completed)', 'p': 34, 'result': 5702887, 'duration': 8.584540605545044, 'pid': 2895907, 'ppid': 1537078}
# 18:56:33 [    INFO] (dbos:main.py:80) {'message': 'Parallel Workflow Result (as completed)', 'p': 34, 'result': 5702887, 'duration': 7.941507816314697, 'pid': 2895907, 'ppid': 1537078}
