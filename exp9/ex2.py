import random
import time
from typing import Dict, List

from dbos import DBOS, DBOSClient, DBOSConfig, Queue, WorkflowHandle
from faker import Faker

fake = Faker()
Faker.seed(123)

random.seed(12)

queue = Queue("my_queue", worker_concurrency=1)


@DBOS.dbos_class()
class Fetcher:
    credentials: Dict[str, str] = {}

    def __init__(self, credentials: Dict[str, str] = None):
        if credentials:
            self.credentials = credentials
        else:
            # Generate fake credentials
            self.credentials = {
                "fake_name": fake.name(),
                "fake_cc": fake.credit_card_number(card_type="mastercard"),
                "prefix": fake.word(),
            }

    @DBOS.step(retries_allowed=True, interval_seconds=1)
    def fetch(self, url: str) -> str:
        DBOS.logger.info(
            f"Step: Fetching URL: {url} with credentials: {self.credentials} :: {DBOS.step_status.current_attempt}/{DBOS.step_status.max_attempts}"
        )
        if url.endswith("/9"):
            DBOS.logger.error(f"URL is too long: {url}")
            if DBOS.step_status.current_attempt < DBOS.step_status.max_attempts - 1:
                raise ValueError(f"URL is too long: {url}")
            else:
                # simulate OOM error
                import ctypes

                ctypes.string_at(0)

        # Simulate fetching data from a URL
        time.sleep(0.1)
        return {"name": fake.name(), "address": fake.address(), "url": url}

    def fetch_urls(self, n: int = 10) -> List[dict]:
        fake_urls = [f"https://{self.credentials['prefix']}.com/{i}" for i in range(n)]
        results = []
        for url in fake_urls:
            DBOS.logger.info(f"Method: Fetching URL: {url} of {n} URLs")
            result = self.fetch(url)
            DBOS.logger.info(f"Method: Fetched data: {result}")
            results.append(result)
        return results


@DBOS.workflow(max_recovery_attempts=2)
def fetch_workflow(n: int = 10) -> List[dict]:
    """Workflow to fetch multiple URLs with credentials"""
    fetcher = Fetcher({"real_creds": "real_creds_value", "prefix": "real_prefix"})
    results = fetcher.fetch_urls(n)
    DBOS.logger.info("Workflow: All URLs fetched successfully.")
    return results


if __name__ == "__main__":
    config: DBOSConfig = {
        "name": "fibonacci-server",
        "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
    }
    DBOS(config=config)
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
    handle: WorkflowHandle = queue.enqueue(fetch_workflow, n=11)
    DBOS.logger.info(
        f"Main: Enqueued Workflow with ID: {handle.workflow_id} and status: {handle.get_status().status}"
    )
    output = handle.get_result()
    DBOS.logger.info(f"Main: Fetch Workflow completed with output: {output}")
