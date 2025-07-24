import asyncio
import random
from typing import Dict, List

from dbos import DBOS, DBOSClient, DBOSConfig, Queue, WorkflowHandleAsync
from faker import Faker

fake = Faker()
Faker.seed(123)

# random.seed(12)

# This does not work.
# > you are not supposed to call asyncio.gather in a workflow. Because it’s nondeterministic. The steps could finish in any order and DBOS can’t recover such a workflow.

queue = Queue("my_queue", worker_concurrency=1)

config: DBOSConfig = {
    "name": "experiment-fetcher",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


@DBOS.dbos_class()
class Fetcher:
    credentials: Dict[str, str] = {}

    def __init__(self, credentials: Dict[str, str] = None):
        if credentials:
            self.credentials = credentials
        else:
            # Generate fake credentials
            self.credentials = {
                "fake_creds": fake.credit_card_number(card_type="mastercard"),
            }

    @DBOS.step(retries_allowed=True, interval_seconds=1)
    async def fetch(self, url: str) -> str:
        DBOS.logger.info(
            f"Step: Fetching URL: {url} with credentials: {self.credentials} :: {DBOS.step_status.current_attempt}/{DBOS.step_status.max_attempts}"
        )
        # if url.endswith(".html"):
        #     DBOS.logger.error(f"Step: Simulated error: {url}")
        #     # if DBOS.step_status.current_attempt < DBOS.step_status.max_attempts - 1:
        #     #     raise ValueError(f"Simulated error for URL: {url}")
        #     # else:
        #     #     # simulate OOM error
        #     #     import ctypes

        #     #     ctypes.string_at(0)
        #     raise ValueError(f"Simulated error for URL: {url}")
        if (
            random.choice([True, False, False, False])  # 1 in 4 chance
            and DBOS.step_status.current_attempt < DBOS.step_status.max_attempts - 1
        ):
            DBOS.logger.error(f"Step: Simulated error for URL: {url}")
            raise ValueError(f"Simulated error for URL: {url}")

        # Simulate fetching data from a URL
        await asyncio.sleep(random.uniform(0.5, 1))  # Simulate network delay
        result = {"name": fake.name(), "url": url}
        DBOS.logger.info(f"Step: Result len: {result}")
        return result

    async def fetch_urls(self, n: int = 10) -> List[dict]:
        tasks = []

        DBOS.logger.info(f"Method: Fetching {n} URLs concurrently")

        async def _generate_url(ulr: str):
            await asyncio.sleep(random.uniform(0.5, 1))  # Simulate work delay
            return await self.fetch(ulr)

        DBOS.logger.info("Method: Generating URLs")

        for ulr in [fake.uri() for _ in range(n)]:
            task = _generate_url(ulr)
            tasks.append(task)

        DBOS.logger.info(f"Method: Gathering results for {len(tasks)} URLs")

        # results = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                DBOS.logger.info(f"Method: Fetched data: {result}")
                results.append(result)
            except Exception as e:
                DBOS.logger.error(f"Method: Error fetching URL: {e}")

        DBOS.logger.info(f"Method: Fetched {len(results)} URLs")
        return results


@DBOS.workflow(max_recovery_attempts=2)
async def fetch_workflow(n: int = 10) -> List[dict]:
    """Workflow to fetch multiple URLs with credentials"""
    DBOS.logger.info("Workflow: Starting to fetch URLs")
    fetcher = Fetcher({"real_creds": "real_creds_value"})
    results = await fetcher.fetch_urls(n)
    DBOS.logger.info(
        f"Workflow: All URLs fetched successfully: {len(results)} results of {n} requested"
    )
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
    handle: WorkflowHandleAsync = await queue.enqueue_async(fetch_workflow, n=11)
    DBOS.logger.info(
        f"Main: Enqueued Workflow with ID: {handle.workflow_id} and status: {(await handle.get_status()).status}"
    )
    output = await handle.get_result()
    DBOS.logger.info("Main: Fetch Workflow completed with output:")

    for idx, item in enumerate(output):
        DBOS.logger.info(f"Main: Result {idx + 1}: {item}")


if __name__ == "__main__":
    asyncio.run(main())
