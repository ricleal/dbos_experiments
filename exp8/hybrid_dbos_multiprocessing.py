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
    return n, result


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
        DBOS.logger.info(
            dict(
                message="Hybrid Workflow Results",
                workflow_idx=workflow_idx,
                results=workflow_results,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )
