import os
import pprint
import random
from time import sleep

from dbos import DBOS, DBOSConfig, DBOSConfiguredInstance, WorkflowHandle
from faker import Faker

fake = Faker()
Faker.seed(123)
random.seed(3)

# contrary to doc
# > DBOS-decorated classes must be instantiated before DBOS.launch() is called.


@DBOS.dbos_class()
class URLFetcher(DBOSConfiguredInstance):
    def __init__(self, name: str):
        self.name = name
        super().__init__(config_name=name)

    @DBOS.workflow()
    def fetch_workflows(self) -> dict:
        results = {}
        for _ in range(10):
            url = fake.uri()
            result = self.fetch_url(url)
            DBOS.logger.info(f"Workflow: Fetched data: {result}")
            results[url] = result
            # Simulate a OOM error
            if random.random() < 0.01:
                import ctypes

                ctypes.string_at(0)
            # End simulate
        return results

    @DBOS.step()
    def fetch_url(self, url: str) -> str:
        # Simulate network delay
        sleep(0.1)
        if random.random() < 0.05:
            raise ValueError("Simulated fetch error")
        return fake.first_name()


if __name__ == "__main__":
    DBOS.logger.info("Main: Starting")
    config: DBOSConfig = {
        "name": "dbos-starter",
        "database_url": os.getenv(
            "DBOS_DATABASE_URL",
            "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        ),
        "log_level": "DEBUG",
    }
    DBOS(config=config)
    DBOS.launch()

    # The log warns against creating DBOS-decorated instances after launch
    # > Configured instance MyFetcher of class URLFetcher was registered after DBOS was launched.
    # > This may cause errors during workflow recovery. All configured instances should be instantiated before DBOS is launched.
    url_fetcher = URLFetcher(name="MyFetcher")
    handle: WorkflowHandle = DBOS.start_workflow(url_fetcher.fetch_workflows)

    output = handle.get_result()
    DBOS.logger.info("Main: Workflow output:")
    pprint.pprint(output)
