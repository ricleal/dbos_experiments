import asyncio
import os
import random
from typing import List, Tuple

from dbos import DBOSClient, EnqueueOptions


async def main():
    # Initialize DBOS client
    client = DBOSClient(
        database_url="postgresql://trustle:trustle@localhost:5432/test?sslmode=disable"
    )

    print(f"Client started with PID: {os.getpid()}")

    # Generate random fibonacci numbers to calculate
    fibonacci_numbers = [random.randint(25, 40) for _ in range(5)]

    print(f"Requesting fibonacci calculations for: {fibonacci_numbers}")

    options: EnqueueOptions = {
        "queue_name": "my_queue",
        "workflow_name": "fibonacci_workflow",
    }

    # Start workflows for each fibonacci number
    workflow_handles = []
    for n in fibonacci_numbers:
        print(f"Starting fibonacci calculation for n={n}")

        handle = await client.enqueue_async(options, n)

        workflow_handles.append((n, handle))
        print(f"Started workflow {handle.workflow_id} for fibonacci({n})")

    # Wait for all results
    results: List[Tuple[int, int, float]] = []
    for original_n, handle in workflow_handles:
        print(
            f"Waiting for result of fibonacci({original_n}) from workflow {handle.workflow_id}"
        )

        result = await handle.get_result()
        results.append(result)

        n, fib_result, duration = result
        print(f"Received result: fibonacci({n}) = {fib_result} (took {duration:.3f}s)")

    # Display summary
    print("\n=== Summary ===")
    for n, result, duration in results:
        print(f"fibonacci({n}) = {result} (duration: {duration:.3f}s)")

    total_duration = sum(duration for _, _, duration in results)
    print(f"Total computation time: {total_duration:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())
