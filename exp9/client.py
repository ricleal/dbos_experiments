import asyncio
import os
from typing import List, Tuple

from dbos import DBOSClient, EnqueueOptions, WorkflowHandleAsync


async def main():
    # Initialize DBOS client
    client = DBOSClient(
        database_url="postgresql://trustle:trustle@localhost:5432/test?sslmode=disable"
    )

    print(f"Client started with PID: {os.getpid()}")

    # Generate random fibonacci numbers to calculate
    # fibonacci_numbers = [random.randint(30, 50) for _ in range(10)]
    # fibonacci_numbers = list(range(35, 41))  # Example range, can be adjusted
    fibonacci_numbers = [100]

    print(f"Requesting fibonacci calculations for: {fibonacci_numbers}")

    options: EnqueueOptions = {
        "queue_name": "my_queue",
        "workflow_name": "fibonacci_workflow",
    }

    # Start workflows for each fibonacci number
    workflow_handles = []
    for n in fibonacci_numbers:
        print(f"Starting fibonacci calculation for n={n}")

        handle = await client.enqueue_async(options, n=n)

        workflow_handles.append((n, handle))
        print(f"Started workflow {handle.workflow_id} for fibonacci({n})")

    # Wait for all results - process them as they complete
    results: List[Tuple[int, int, float]] = []

    # Create async tasks for getting results
    async def get_result_with_context(original_n: int, handle: WorkflowHandleAsync):
        result = await handle.get_result()
        return original_n, handle.workflow_id, result

    tasks = [
        get_result_with_context(original_n, handle)
        for original_n, handle in workflow_handles
    ]

    # Process results as they complete
    for task in asyncio.as_completed(tasks):
        original_n, workflow_id, result = await task
        results.append(result)

        n, fib_result, duration = result
        print(
            f"✅ Completed: fibonacci({n}) = {fib_result} (took {duration:.3f}s) [workflow {workflow_id}]"
        )

    # Display summary
    print("\n=== Summary ===")
    for n, result, duration in results:
        print(f"fibonacci({n}) = {result} (duration: {duration:.3f}s)")

    total_duration = sum(duration for _, _, duration in results)
    print(f"Total computation time: {total_duration:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())
