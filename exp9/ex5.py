import asyncio
import random
from typing import List

from dbos import DBOS, DBOSClient, DBOSConfig, Queue, WorkflowHandleAsync
from faker import Faker

fake = Faker()
Faker.seed(123)

queue = Queue("my_queue", worker_concurrency=1)

config: DBOSConfig = {
    "name": "experiment-fetcher",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


@DBOS.step(retries_allowed=True, interval_seconds=1)
async def specific_step() -> str:
    """A specific step that does something"""
    DBOS.logger.info("Step: Executing specific step")
    return fake.sentence()


@DBOS.workflow(max_recovery_attempts=2)
def specific_workflow(n: int) -> str:
    """A specific workflow that does something"""
    DBOS.logger.info(f"Workflow: Starting specific workflow with n={n}")
    result = specific_step()
    DBOS.logger.info(f"Workflow: Completed specific workflow with result: {result}")
    return 2 * result


@DBOS.step()
async def process(i: int) -> str:
    DBOS.logger.info(f"Step: Processing item {i}")
    # Simulate processing time
    await asyncio.sleep(random.uniform(0.1, 0.5))
    r = specific_workflow(i)
    result = {"index": i, "result": r}
    DBOS.logger.info(f"Step: Processed item {i} with result: {result}")
    return result


@DBOS.workflow(max_recovery_attempts=2)
async def do_it_all(n: int = 10) -> List[dict]:
    """Workflow to fetch multiple URLs with credentials"""
    DBOS.logger.info("Workflow: Starting do_it_all workflow")
    results = []
    for i in range(n):
        result = await process(i)
        results.append(result)
    DBOS.logger.info(f"Workflow: Completed do_it_all workflow with results: {results}")
    return results


async def main():
    DBOS.launch()

    # Get the queue details
    DBOS.logger.info("Main: Queue details")
    client = DBOSClient(
        "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable"
    )
    queued_workflows = client.list_queued_workflows(queue_name=queue.name)
    DBOS.logger.info(
        f"Main: Queued Workflows: {len(queued_workflows)} in queue '{queue.name}'"
    )

    DBOS.logger.info("Starting Fetch Workflow")
    handle: WorkflowHandleAsync = await queue.enqueue_async(do_it_all, n=11)
    DBOS.logger.info(
        f"Main: Enqueued Workflow with ID: {handle.workflow_id} and status: {(await handle.get_status()).status}"
    )
    output = await handle.get_result()
    DBOS.logger.info("Main: Fetch Workflow completed with output:")

    for idx, item in enumerate(output):
        DBOS.logger.info(f"Main: Result {idx + 1}: {item}")


if __name__ == "__main__":
    asyncio.run(main())
