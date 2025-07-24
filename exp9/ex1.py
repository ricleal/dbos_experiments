import os
import random
import time
from typing import Tuple

from dbos import DBOS, DBOSConfig, DBOSConfiguredInstance, Queue

"""
This does not work.
The class FibonacciCalculator is instanciated in the main process before launch()

When it fails and the step `calculate_i` is called again, it tries to access the `self.memo` attribute which
does not exist, because the class is not instantiated.

"""


config: DBOSConfig = {
    "name": "fibonacci-server",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


queue = Queue("my_queue", worker_concurrency=1)

random.seed(1234)  # For reproducibility in random number generation


@DBOS.dbos_class()
class FibonacciCalculator(DBOSConfiguredInstance):
    """Class for calculating fibonacci numbers with timing"""

    def __init__(self):
        self.memo = {}
        self.name = "fibonacci_calculator"
        super().__init__(config_name=self.name)

    @DBOS.step(retries_allowed=True, interval_seconds=1)
    def calculate_i(self, i: int):
        if i not in self.memo:
            print(f"{self.name}: calculating fibonacci({i})")
            self.memo[i] = self.memo[i - 1] + self.memo[i - 2]
            print(
                f"{self.name}: calculated and memoized fibonacci({i}) = {self.memo[i]}"
            )
        ## simulate an error
        if i > 10:
            r = random.randint(0, i)
            if i == r:
                print(f"\t{self.name}: simulating error for fibonacci({i})")
                # os.kill(os.getppid(), signal.SIGTERM)
                # sys.exit(1)  # Simulate a crash
                # raise Exception(f"Simulated error for fibonacci({i})")
                # Option 3: Segmentation fault (most realistic)
                import ctypes

                ctypes.string_at(0)

        return self.memo[i]

    def fibonacci_memoization(self, n):
        """
        Calculates the nth Fibonacci number using memoization with iterative approach.

        Args:
            n (int): The index of the Fibonacci number to calculate.

        Returns:
            int: The nth Fibonacci number.
        """
        if n <= 0:
            return 0
        elif n == 1:
            return 1

        # Check if already computed
        if n in self.memo:
            print(f"Using memoized value for fibonacci({n})")
            return self.memo[n]

        # Initialize base cases if not in memo
        if 0 not in self.memo:
            self.memo[0] = 0
        if 1 not in self.memo:
            self.memo[1] = 1

        total = 0
        # Iteratively calculate fibonacci numbers up to n
        for i in range(2, n + 1):
            total = self.calculate_i(i)

        return total

    @DBOS.workflow()
    def calculate_fibonacci(self, n: int) -> Tuple[int, int, float]:
        """Step that calculates fibonacci number and measures duration"""
        DBOS.logger.info(
            dict(
                message="Starting fibonacci calculation",
                n=n,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )

        start_time = time.time()
        result = self.fibonacci_memoization(n)
        duration = time.time() - start_time

        DBOS.logger.info(
            dict(
                message="Fibonacci calculation completed",
                n=n,
                result=result,
                duration=duration,
                pid=os.getpid(),
                ppid=os.getppid(),
            )
        )

        return n, result, duration


# DBOS-decorated classes must be instantiated before DBOS.launch() is called.
f = FibonacciCalculator()


@DBOS.workflow()
def fibonacci_workflow(n: int) -> Tuple[int, int, float]:
    """Workflow that calculates fibonacci number"""
    DBOS.logger.info(
        dict(
            message="Fibonacci Workflow Started",
            wf_id=DBOS.workflow_id,
            n=n,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    result = f.calculate_fibonacci(n)

    DBOS.logger.info(
        dict(
            message="Fibonacci Workflow Completed",
            wf_id=DBOS.workflow_id,
            n=result[0],
            result=result[1],
            duration=result[2],
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    return result


def main():
    DBOS.launch()

    DBOS.logger.info("Starting Fibonacci Workflows")

    n = 100  # Example value, can be adjusted
    handle = queue.enqueue(fibonacci_workflow, n)

    result = handle.get_result()
    n, fib_result, duration = result

    DBOS.logger.info(
        dict(
            message="Fibonacci Workflow Result",
            n=n,
            result=fib_result,
            duration=duration,
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )


if __name__ == "__main__":
    main()
