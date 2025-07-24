import time
from typing import Dict, List

from dbos import (
    DBOS,
    DBOSConfig,
    DBOSConfiguredInstance,
    Queue,
    WorkflowHandle,
)
from faker import Faker

fake = Faker()
Faker.seed(123)

queue = Queue("my_queue", worker_concurrency=1)


@DBOS.dbos_class()
class Fetcher(DBOSConfiguredInstance):
    credentials: Dict[str, str] = {}

    def __init__(self, credentials: Dict[str, str] = None):
        if credentials:
            self.credentials = credentials
        else:
            # Generate fake credentials
            self.credentials = {
                "fake_name": fake.name(),
                "fake_cc": fake.credit_card_number(card_type="mastercard"),
            }
        super().__init__(config_name="fetcher")

    @DBOS.step(retries_allowed=True, interval_seconds=1)
    def fetch(self, url: str) -> str:
        DBOS.logger.info(
            f"Step: Fetching URL: {url} with credentials: {self.credentials}"
        )
        if url.endswith("/9"):
            DBOS.logger.error(f"URL is too long: {url}")
            raise ValueError(f"URL is too long: {url}")

        # Simulate fetching data from a URL
        time.sleep(0.1)
        return {"name": fake.name(), "address": fake.address(), "url": url}

    # @DBOS.workflow()
    def fetch_urls(self, n: int = 10) -> List[dict]:
        fake_urls = [f"https://example.com/{i}" for i in range(n)]
        results = []
        for url in fake_urls:
            DBOS.logger.info(f"Method: Fetching URL: {url}")
            result = self.fetch(url)
            DBOS.logger.info(f"Method: Fetched data: {result}")
            results.append(result)
        return results


@DBOS.workflow(max_recovery_attempts=2)
def fetch_workflow(fetcher: Fetcher, n: int = 10) -> List[dict]:
    """Workflow to fetch multiple URLs with credentials"""
    results = fetcher.fetch_urls(n)
    DBOS.logger.info("Workflow: All URLs fetched successfully.")
    return results


if __name__ == "__main__":
    config: DBOSConfig = {
        "name": "fibonacci-server",
        "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
    }
    DBOS(config=config)

    f = Fetcher(credentials={"username": "user", "password": "pass"})
    DBOS.launch()

    DBOS.logger.info("Starting Fetch Workflow")
    handle: WorkflowHandle = queue.enqueue(fetch_workflow, fetcher=f, n=10)
    DBOS.logger.info(
        f"Main: Enqueued Workflow with ID: {handle.workflow_id} and status: {handle.get_status().status}"
    )
    output = handle.get_result()
    DBOS.logger.info(f"Main: Fetch Workflow completed with output: {output}")
