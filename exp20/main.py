import asyncio
import random
from typing import Tuple

from dbos import DBOS, DBOSConfig, Queue, WorkflowHandleAsync
from faker import Faker

fake = Faker()
Faker.seed(123)
random.seed(3)

# Global concurrency limits the total number of workflows from a queue that can run concurrently across all DBOS processes in your application.
# Worker concurrency sets the maximum number of workflows from a queue that can run concurrently on a single DBOS process.
queue = Queue("my_queue", concurrency=10, worker_concurrency=10)


config: DBOSConfig = {
    "name": "dbos-starter",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
    # "log_level": "DEBUG",
}
DBOS(config=config)


@DBOS.step()
async def fetch_url(url: str) -> float:
    """Simulated step that 'fetches' a URL and returns the simulated delay"""
    delay = random.uniform(0.1, 0.5)  # Simulate network delay
    # delay = 0.2
    await asyncio.sleep(delay)
    return delay


@DBOS.workflow()
async def workflow_instance(instance_id: int) -> Tuple[int, float]:
    DBOS.logger.info(
        dict(
            message="Workflow Started",
            wf_id=DBOS.workflow_id,
            instance_id=instance_id,
        )
    )
    total_delay = sum([await fetch_url(fake.url()) for _ in range(5)])
    DBOS.logger.info(
        dict(
            message="Workflow Completed",
            wf_id=DBOS.workflow_id,
            instance_id=instance_id,
            total_delay=total_delay,
        )
    )
    return instance_id, total_delay


async def main():
    DBOS.launch()

    DBOS.logger.info(
        dict(
            message="Starting Workflows",
            queue_name=queue.name,
            concurrency=queue.concurrency,
            worker_concurrency=queue.worker_concurrency,
        )
    )

    n_workflows = 10

    real_time_start = asyncio.get_event_loop().time()
    task_handles = []
    for i in range(n_workflows):
        handle: WorkflowHandleAsync = await queue.enqueue_async(workflow_instance, i)
        task_handles.append(handle)

    real_time_enqueue_end = asyncio.get_event_loop().time()
    real_time_enqueue_elapsed = real_time_enqueue_end - real_time_start

    DBOS.logger.info(
        dict(
            message="All Workflows Enqueued",
            total_workflows=len(task_handles),
            real_time_enqueue_elapsed=real_time_enqueue_elapsed,
            n_workflows=n_workflows,
        )
    )

    total_workflows_delay = 0.0
    for coro in asyncio.as_completed([handle.get_result() for handle in task_handles]):
        instance_id, total_delay = await coro
        DBOS.logger.info(
            dict(
                message="Workflow Result",
                instance_id=instance_id,
                total_delay=total_delay,
            )
        )
        total_workflows_delay += total_delay

    real_time_end = asyncio.get_event_loop().time()
    real_time_elapsed = real_time_end - real_time_start

    DBOS.logger.info(
        dict(
            message="All Workflows Completed",
            total_main_delay=total_workflows_delay,
            real_time_elapsed=real_time_elapsed,
            real_time_enqueue_elapsed=real_time_enqueue_elapsed,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
