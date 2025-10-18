import os
import random
import time
from multiprocessing import Pool
from typing import List, Tuple

from dbos import DBOS, DBOSConfig, Queue

config: DBOSConfig = {
    "name": "dbos-multiprocessing-starter",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def parallel_fibonacci_task(n: int) -> Tuple[int, int]:
    """Function to be executed in multiprocessing pool"""
    t = time.time()
    result = fibonacci(n)
    duration = time.time() - t
    DBOS.logger.info(
        dict(
            message="Parallel Fibonacci Task Completed",
            n=n,
            result=result,
            duration=duration,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )
    return n, result, duration


@DBOS.step()
def multiprocessing_fibonacci_step(numbers: List[int]) -> List[Tuple[int, int]]:
    """Step that uses multiprocessing to compute fibonacci numbers"""
    DBOS.logger.info(
        dict(
            message="Starting multiprocessing fibonacci computation",
            numbers=numbers,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    with Pool(processes=5) as pool:
        results = pool.map(parallel_fibonacci_task, numbers)

    DBOS.logger.info(
        dict(
            message="Multiprocessing fibonacci computation completed",
            results_count=len(results),
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    return results


@DBOS.workflow()
def hybrid_workflow() -> List[Tuple[int, int]]:
    """Workflow that combines DBOS durability with multiprocessing performance"""
    DBOS.logger.info(
        dict(
            message="Hybrid Workflow Started",
            wf_id=DBOS.workflow_id,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    # Generate random fibonacci numbers to compute
    numbers = [random.randint(30, 40) for _ in range(10)]

    # Execute multiprocessing step
    results = multiprocessing_fibonacci_step(numbers)

    DBOS.logger.info(
        dict(
            message="Hybrid Workflow Completed",
            wf_id=DBOS.workflow_id,
            pid=os.getpid(),
            ppid=os.getppid(),
            total_results=len(results),
        )
    )

    return results


queue = Queue("hybrid_queue", concurrency=3, worker_concurrency=2)

if __name__ == "__main__":
    DBOS.launch()

    DBOS.logger.info(
        dict(
            message="Starting Hybrid DBOS-Multiprocessing Workflows",
            queue_name=queue.name,
            concurrency=queue.concurrency,
            worker_concurrency=queue.worker_concurrency,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    task_handles = []
    for i in range(3):
        handle = queue.enqueue(hybrid_workflow)
        task_handles.append(handle)

    results = [handle.get_result() for handle in task_handles]

    for workflow_idx, workflow_results in enumerate(results):
        for result in workflow_results:
            n, fib_n, duration = result
            DBOS.logger.info(
                dict(
                    message="▶️ Hybrid Workflow Result",
                    workflow_idx=workflow_idx,
                    n=n,
                    fib_n=fib_n,
                    duration=duration,
                )
            )

# ❯ python exp8/hybrid_dbos_multiprocessing.py
# DBOS system database URL: postgresql://trustle:***@localhost:5432/test_dbos_sys?sslmode=disable
# DBOS application database URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
# Database engine parameters: {'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True, 'connect_args': {'connect_timeout': 10}}
# 19:10:07 [    INFO] (dbos:_dbos.py:370) Initializing DBOS (v2.1.0)
# 19:10:07 [    INFO] (dbos:_dbos.py:445) Executor ID: local_executer
# 19:10:07 [    INFO] (dbos:_dbos.py:446) Application version: local_v0
# 19:10:08 [ WARNING] (dbos:_dbos.py:486) Failed to start admin server: [Errno 98] Address already in use
# 19:10:08 [    INFO] (dbos:_dbos.py:496) No workflows to recover from application version local_v0
# 19:10:08 [    INFO] (dbos:_dbos.py:548) DBOS launched!
# To view and manage workflows, connect to DBOS Conductor at:https://console.dbos.dev/self-host?appname=dbos-multiprocessing-starter
# 19:10:08 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:103) {'message': 'Starting Hybrid DBOS-Multiprocessing Workflows', 'queue_name': 'hybrid_queue', 'concurrency': 3, 'worker_concurrency': 2, 'pid': 2941396, 'ppid': 1537078}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:70) {'message': 'Hybrid Workflow Started', 'wf_id': '5b999c73-dba0-4152-9d6e-8ef3673decdc', 'pid': 2941396, 'ppid': 1537078}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:43) {'message': 'Starting multiprocessing fibonacci computation', 'numbers': [34, 33, 37, 34, 38, 36, 31, 35, 34, 38], 'pid': 2941396, 'ppid': 1537078}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:70) {'message': 'Hybrid Workflow Started', 'wf_id': '7af49cc0-6c20-4bc7-a5d8-03bcb41aa9d7', 'pid': 2941396, 'ppid': 1537078}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:43) {'message': 'Starting multiprocessing fibonacci computation', 'numbers': [30, 40, 33, 37, 30, 39, 39, 37, 32, 32], 'pid': 2941396, 'ppid': 1537078}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 30, 'result': 832040, 'duration': 0.228377103805542, 'pid': 2941420, 'ppid': 2941396}
# 19:10:09 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 30, 'result': 832040, 'duration': 0.23161983489990234, 'pid': 2941424, 'ppid': 2941396}
# 19:10:10 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 33, 'result': 3524578, 'duration': 0.8085527420043945, 'pid': 2941413, 'ppid': 2941396}
# 19:10:10 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 33, 'result': 3524578, 'duration': 0.8253583908081055, 'pid': 2941422, 'ppid': 2941396}
# 19:10:10 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 34, 'result': 5702887, 'duration': 1.261584758758545, 'pid': 2941412, 'ppid': 2941396}
# 19:10:10 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 34, 'result': 5702887, 'duration': 1.2894620895385742, 'pid': 2941415, 'ppid': 2941396}
# 19:10:11 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 31, 'result': 1346269, 'duration': 0.2845480442047119, 'pid': 2941412, 'ppid': 2941396}
# 19:10:12 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 34, 'result': 5702887, 'duration': 1.2600841522216797, 'pid': 2941412, 'ppid': 2941396}
# 19:10:12 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 35, 'result': 9227465, 'duration': 2.1594130992889404, 'pid': 2941415, 'ppid': 2941396}
# 19:10:13 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 36, 'result': 14930352, 'duration': 3.305870771408081, 'pid': 2941413, 'ppid': 2941396}
# 19:10:14 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 37, 'result': 24157817, 'duration': 5.302825212478638, 'pid': 2941414, 'ppid': 2941396}
# 19:10:14 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 37, 'result': 24157817, 'duration': 5.30984902381897, 'pid': 2941423, 'ppid': 2941396}
# 19:10:15 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 32, 'result': 2178309, 'duration': 0.47287893295288086, 'pid': 2941423, 'ppid': 2941396}
# 19:10:15 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 37, 'result': 24157817, 'duration': 5.305846452713013, 'pid': 2941422, 'ppid': 2941396}
# 19:10:15 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 32, 'result': 2178309, 'duration': 0.4901435375213623, 'pid': 2941423, 'ppid': 2941396}
# 19:10:18 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 38, 'result': 39088169, 'duration': 8.686675310134888, 'pid': 2941416, 'ppid': 2941396}
# 19:10:21 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 38, 'result': 39088169, 'duration': 8.8319730758667, 'pid': 2941412, 'ppid': 2941396}
# 19:10:21 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:55) {'message': 'Multiprocessing fibonacci computation completed', 'results_count': 10, 'pid': 2941396, 'ppid': 1537078}
# 19:10:21 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:85) {'message': 'Hybrid Workflow Completed', 'wf_id': '5b999c73-dba0-4152-9d6e-8ef3673decdc', 'pid': 2941396, 'ppid': 1537078, 'total_results': 10}
# 19:10:21 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:70) {'message': 'Hybrid Workflow Started', 'wf_id': '20b6ebaa-b179-4f20-9c79-6d2e99b2322d', 'pid': 2941396, 'ppid': 1537078}
# 19:10:21 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:43) {'message': 'Starting multiprocessing fibonacci computation', 'numbers': [38, 37, 36, 33, 40, 35, 31, 31, 32, 36], 'pid': 2941396, 'ppid': 1537078}
# 19:10:22 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 33, 'result': 3524578, 'duration': 0.8566572666168213, 'pid': 2942293, 'ppid': 2941396}
# 19:10:23 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 39, 'result': 63245986, 'duration': 13.851956367492676, 'pid': 2941424, 'ppid': 2941396}
# 19:10:23 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 39, 'result': 63245986, 'duration': 14.064490556716919, 'pid': 2941420, 'ppid': 2941396}
# 19:10:24 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 35, 'result': 9227465, 'duration': 2.0757815837860107, 'pid': 2942293, 'ppid': 2941396}
# 19:10:24 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 31, 'result': 1346269, 'duration': 0.30190587043762207, 'pid': 2942293, 'ppid': 2941396}
# 19:10:25 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 36, 'result': 14930352, 'duration': 3.3372180461883545, 'pid': 2942292, 'ppid': 2941396}
# 19:10:25 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 31, 'result': 1346269, 'duration': 0.2990593910217285, 'pid': 2942293, 'ppid': 2941396}
# 19:10:25 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 32, 'result': 2178309, 'duration': 0.4667825698852539, 'pid': 2942292, 'ppid': 2941396}
# 19:10:27 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 37, 'result': 24157817, 'duration': 5.404072046279907, 'pid': 2942291, 'ppid': 2941396}
# 19:10:28 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 36, 'result': 14930352, 'duration': 3.4392223358154297, 'pid': 2942293, 'ppid': 2941396}
# 19:10:30 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 38, 'result': 39088169, 'duration': 8.75480031967163, 'pid': 2942290, 'ppid': 2941396}
# 19:10:32 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 40, 'result': 102334155, 'duration': 22.591735124588013, 'pid': 2941421, 'ppid': 2941396}
# 19:10:32 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:55) {'message': 'Multiprocessing fibonacci computation completed', 'results_count': 10, 'pid': 2941396, 'ppid': 1537078}
# 19:10:32 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:85) {'message': 'Hybrid Workflow Completed', 'wf_id': '7af49cc0-6c20-4bc7-a5d8-03bcb41aa9d7', 'pid': 2941396, 'ppid': 1537078, 'total_results': 10}
# 19:10:44 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:27) {'message': 'Parallel Fibonacci Task Completed', 'n': 40, 'result': 102334155, 'duration': 22.952478647232056, 'pid': 2942294, 'ppid': 2941396}
# 19:10:44 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:55) {'message': 'Multiprocessing fibonacci computation completed', 'results_count': 10, 'pid': 2941396, 'ppid': 1537078}
# 19:10:44 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:85) {'message': 'Hybrid Workflow Completed', 'wf_id': '20b6ebaa-b179-4f20-9c79-6d2e99b2322d', 'pid': 2941396, 'ppid': 1537078, 'total_results': 10}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 34, 'fib_n': 5702887, 'duration': 1.261584758758545}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 33, 'fib_n': 3524578, 'duration': 0.8085527420043945}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 37, 'fib_n': 24157817, 'duration': 5.302825212478638}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 34, 'fib_n': 5702887, 'duration': 1.2894620895385742}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 38, 'fib_n': 39088169, 'duration': 8.686675310134888}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 36, 'fib_n': 14930352, 'duration': 3.305870771408081}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 31, 'fib_n': 1346269, 'duration': 0.2845480442047119}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 35, 'fib_n': 9227465, 'duration': 2.1594130992889404}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 34, 'fib_n': 5702887, 'duration': 1.2600841522216797}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 0, 'n': 38, 'fib_n': 39088169, 'duration': 8.8319730758667}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 30, 'fib_n': 832040, 'duration': 0.228377103805542}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 40, 'fib_n': 102334155, 'duration': 22.591735124588013}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 33, 'fib_n': 3524578, 'duration': 0.8253583908081055}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 37, 'fib_n': 24157817, 'duration': 5.30984902381897}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 30, 'fib_n': 832040, 'duration': 0.23161983489990234}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 39, 'fib_n': 63245986, 'duration': 14.064490556716919}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 39, 'fib_n': 63245986, 'duration': 13.851956367492676}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 37, 'fib_n': 24157817, 'duration': 5.305846452713013}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 32, 'fib_n': 2178309, 'duration': 0.47287893295288086}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 1, 'n': 32, 'fib_n': 2178309, 'duration': 0.4901435375213623}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 38, 'fib_n': 39088169, 'duration': 8.75480031967163}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 37, 'fib_n': 24157817, 'duration': 5.404072046279907}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 36, 'fib_n': 14930352, 'duration': 3.3372180461883545}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 33, 'fib_n': 3524578, 'duration': 0.8566572666168213}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 40, 'fib_n': 102334155, 'duration': 22.952478647232056}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 35, 'fib_n': 9227465, 'duration': 2.0757815837860107}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 31, 'fib_n': 1346269, 'duration': 0.30190587043762207}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 31, 'fib_n': 1346269, 'duration': 0.2990593910217285}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 32, 'fib_n': 2178309, 'duration': 0.4667825698852539}
# 19:10:45 [    INFO] (dbos:hybrid_dbos_multiprocessing.py:124) {'message': '▶️ Hybrid Workflow Result', 'workflow_idx': 2, 'n': 36, 'fib_n': 14930352, 'duration': 3.4392223358154297}
