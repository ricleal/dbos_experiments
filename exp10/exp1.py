import time
from multiprocessing import Process
from multiprocessing import Queue as MPQueue

from dbos import DBOS, DBOSConfig, Queue, WorkflowStatus, _utils

# Error in step:
#  * exception: retried without replaying
#  * OOM: retried with replaying
# In a Workflow
#  * exception: is like success. The workflow finishes early
#  * OOM: is retried without replying the steps already completed
# Error in the 2nd step:
#  * OOM: Step 1 is assumed to have executed successfully

# Let's make this constant so all retried stuff uses this executable
_utils.GlobalParams.executor_id = "local-executor"
_utils.GlobalParams.app_version = "1.0.0"

queue = Queue("queue")

config: DBOSConfig = {
    "name": "dbos-starter",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_process(n: int) -> int:
    """fork this process and run the Fibonacci calculation in a separate process"""
    # Create a queue to receive the result from the child process
    result_queue = MPQueue()

    def worker(n: int, queue: MPQueue):
        """Worker function that runs in the forked process"""
        result = fibonacci(n)
        queue.put(result)

    # Create and start the child process
    process = Process(target=worker, args=(n, result_queue))
    process.start()

    # Wait for the process to complete and get the result
    result = result_queue.get()
    process.join()

    return result


@DBOS.step(retries_allowed=True)
def step_one(n):
    s = DBOS.step_status
    DBOS.logger.info(
        f"Step 1: n={n}, step_id={s.step_id}, current_attempt={s.current_attempt}, max_attempts={s.max_attempts}"
    )
    return fibonacci_process(n)


@DBOS.step(retries_allowed=True)
def step_two(n):
    s = DBOS.step_status
    DBOS.logger.info(
        f"Step 2: n={n}, step_id={s.step_id}, current_attempt={s.current_attempt}, max_attempts={s.max_attempts}"
    )
    # # Simulate OOM error
    # if n == 10:
    #     import ctypes

    #     ctypes.string_at(0)
    return fibonacci(n)


@DBOS.workflow(max_recovery_attempts=3)
def dbos_workflow(n):
    s: WorkflowStatus = DBOS.get_workflow_status(workflow_id=DBOS.workflow_id)
    DBOS.logger.info(
        f"Workflow: n={n}, name={s.name}, status={s.status}, recovery_attempts={s.recovery_attempts}"
    )
    for i in range(n, n // 3, -1):
        r = step_one(i)
        DBOS.logger.info(f"\tStep 1 result for n={i}: {r}")

    # raise ValueError("Simulated failure in step one")
    # # simulate OOM error
    # import ctypes

    # ctypes.string_at(0)

    for i in range(n // 3, -1, -1):
        r = step_two(i)
        DBOS.logger.info(f"\tStep 2 result for n={i}: {r}")


if __name__ == "__main__":
    DBOS.launch()
    n = 35

    # Check for pending workflows in the queue
    pending_workflows = DBOS.list_queued_workflows(
        queue_name="queue", status=["ENQUEUED", "PENDING"]
    )

    if pending_workflows:
        DBOS.logger.info(
            f"Found {len(pending_workflows)} pending workflows. Waiting for them to complete..."
        )
        # Wait for pending workflows to complete
        for workflow_status in pending_workflows:
            try:
                handle = DBOS.retrieve_workflow(workflow_status.workflow_id)
                DBOS.logger.info(
                    f"Waiting for workflow {workflow_status.workflow_id} to complete..."
                )
                handle.get_result()
                DBOS.logger.info(f"Workflow {workflow_status.workflow_id} completed")
            except Exception as e:
                DBOS.logger.error(
                    f"Error waiting for workflow {workflow_status.workflow_id}: {e}"
                )
    else:
        DBOS.logger.info("No pending workflows found in queue")

    # Now enqueue the new workflow
    DBOS.logger.info(f"Enqueueing new workflow with n={n}")
    handle = queue.enqueue(dbos_workflow, n)

    result = handle.get_result()

    # Let this run until I press Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # DBOS.destroy()
        pass
