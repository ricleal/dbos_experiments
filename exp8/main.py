import os
import random
import time
from typing import Tuple

from dbos import DBOS, DBOSConfig, Queue

config: DBOSConfig = {
    "name": "dbos-starter",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
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
    return p, res


queue = Queue("my_queue", concurrency=10, worker_concurrency=5)

if __name__ == "__main__":
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
        handle = queue.enqueue(parallel_workflow)
        task_handles.append(handle)
    results = [handle.get_result() for handle in task_handles]

    for p, res in results:
        DBOS.logger.info(
            dict(
                message="Parallel Workflow Result",
                p=p,
                result=res,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )

# ❯ python exp8/main.py
# Using database connection string: postgresql://trustle:***@localhost:5432/test?sslmode=disable
# Database engine parameters: {'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True, 'connect_args': {'connect_timeout': 10}}
# 22:23:10 [    INFO] (dbos:_dbos.py:341) Initializing DBOS (v1.7.0)
# 22:23:10 [    INFO] (dbos:_dbos.py:420) Executor ID: local
# 22:23:10 [    INFO] (dbos:_dbos.py:421) Application version: 4876d4fa19aa8bb6a85ce500d7299e47
# 22:23:10 [    INFO] (dbos:_dbos.py:466) No workflows to recover from application version 4876d4fa19aa8bb6a85ce500d7299e47
# 22:23:10 [    INFO] (dbos:_dbos.py:518) DBOS launched!
# To view and manage workflows, connect to DBOS Conductor at: https://console.dbos.dev/self-host?appname=dbos-starter
# 22:23:10 [    INFO] (dbos:main.py:52) {'message': 'Starting Parallel Workflows', 'queue_name': 'my_queue', 'concurrency': 10, 'worker_concurrency': 5, 'pid': 814116, 'ppid': 796045}
# 22:23:11 [    INFO] (dbos:main.py:23) {'message': 'Parallel Workflow Started', 'wf_id': '8747ad45-398d-4b62-baca-8228fe4b319c', 'pid': 814116, 'ppid': 796045}
# 22:23:11 [    INFO] (dbos:main.py:23) {'message': 'Parallel Workflow Started', 'wf_id': '3ed4a431-2e8f-473a-bc14-c79aae11c3d8', 'pid': 814116, 'ppid': 796045}
# 22:23:12 [    INFO] (dbos:main.py:23) {'message': 'Parallel Workflow Started', 'wf_id': '9df45963-cb60-4866-a4ca-d8a59f7db76f', 'pid': 814116, 'ppid': 796045}
# 22:23:12 [    INFO] (dbos:main.py:23) {'message': 'Parallel Workflow Started', 'wf_id': '94839e37-f65b-4215-862c-5eca17401e54', 'pid': 814116, 'ppid': 796045}
# 22:23:13 [    INFO] (dbos:main.py:23) {'message': 'Parallel Workflow Started', 'wf_id': 'dee51e2b-7946-4ed7-a8e7-21b7eb006f94', 'pid': 814116, 'ppid': 796045}
# 22:23:14 [    INFO] (dbos:main.py:35) {'message': 'Parallel Workflow Completed', 'wf_id': '9df45963-cb60-4866-a4ca-d8a59f7db76f', 'pid': 814116, 'ppid': 796045, 'duration': 2.704521656036377}
# 22:23:15 [    INFO] (dbos:main.py:35) {'message': 'Parallel Workflow Completed', 'wf_id': '8747ad45-398d-4b62-baca-8228fe4b319c', 'pid': 814116, 'ppid': 796045, 'duration': 3.877823829650879}
# 22:23:15 [    INFO] (dbos:main.py:35) {'message': 'Parallel Workflow Completed', 'wf_id': '94839e37-f65b-4215-862c-5eca17401e54', 'pid': 814116, 'ppid': 796045, 'duration': 3.260852098464966}
# 22:23:28 [    INFO] (dbos:main.py:35) {'message': 'Parallel Workflow Completed', 'wf_id': '3ed4a431-2e8f-473a-bc14-c79aae11c3d8', 'pid': 814116, 'ppid': 796045, 'duration': 16.87392234802246}
# 22:23:29 [    INFO] (dbos:main.py:35) {'message': 'Parallel Workflow Completed', 'wf_id': 'dee51e2b-7946-4ed7-a8e7-21b7eb006f94', 'pid': 814116, 'ppid': 796045, 'duration': 16.410602807998657}
# 22:23:30 [    INFO] (dbos:main.py:70) {'message': 'Parallel Workflow Result', 'p': 32, 'result': 2178309, 'pid': 814116, 'ppid': 796045}
# 22:23:30 [    INFO] (dbos:main.py:70) {'message': 'Parallel Workflow Result', 'p': 36, 'result': 14930352, 'pid': 814116, 'ppid': 796045}
# 22:23:30 [    INFO] (dbos:main.py:70) {'message': 'Parallel Workflow Result', 'p': 30, 'result': 832040, 'pid': 814116, 'ppid': 796045}
# 22:23:30 [    INFO] (dbos:main.py:70) {'message': 'Parallel Workflow Result', 'p': 31, 'result': 1346269, 'pid': 814116, 'ppid': 796045}
# 22:23:30 [    INFO] (dbos:main.py:70) {'message': 'Parallel Workflow Result', 'p': 36, 'result': 14930352, 'pid': 814116, 'ppid': 796045}
