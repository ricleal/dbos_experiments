import json
import multiprocessing
import os
import random
import signal
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from dbos import DBOS, DBOSConfig, Queue, _utils

"""
This does not work.
The class FibonacciCalculator is instanciated in the main process before launch()

When it fails and the step `calculate_i` is called again, it tries to access the `self.memo` attribute which
does not exist, because the class is not instantiated.

"""

# Initialize DBOS with a unique executor ID
_utils.GlobalParams.executor_id = "1"  # str(uuid.uuid4())

config: DBOSConfig = {
    "name": "fibonacci-server",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


Queue("my_queue", worker_concurrency=1)

random.seed(1234)  # For reproducibility in random number generation


class FibonacciCalculator:
    """Class for calculating fibonacci numbers with timing"""

    def __init__(self):
        self.memo = {}

    @DBOS.step(retries_allowed=True, interval_seconds=1)
    def calculate_i(self, i: int):
        if i not in self.memo:
            self.memo[i] = self.memo[i - 1] + self.memo[i - 2]
            print(f"Calculated and memoized fibonacci({i}) = {self.memo[i]}")
        ## simulate an error
        if i > 10:
            r = random.randint(0, i)
            if i == r:
                print(f"Simulating error for fibonacci({i})")
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

    def calculate_fibonacci_step(self, n: int) -> Tuple[int, int, float]:
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

    result = f.calculate_fibonacci_step(n)

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


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "pid": os.getpid(),
                "ppid": os.getppid(),
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()


def health_server_process():
    """Run the health server in a separate process"""
    print(f"Health server starting with PID: {os.getpid()}")

    def signal_handler(signum, frame):
        print(f"Health server received signal {signum}, shutting down...")
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = HTTPServer(("localhost", 8080), HealthHandler)
    print("Health server running on http://localhost:8080/health")
    server.serve_forever()


def fibonacci_server_process():
    """Run the fibonacci DBOS server in a separate process"""

    DBOS.logger.info(
        dict(
            message="Starting Fibonacci Server Process",
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )

    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        DBOS.logger.info(
            dict(
                message="Fibonacci server received signal, shutting down gracefully",
                signal=signum,
                pid=os.getpid(),
            )
        )
        DBOS.destroy()
        exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    DBOS.launch()

    # Keep the server running
    import threading

    threading.Event().wait()


if __name__ == "__main__":
    print(f"Main process starting with PID: {os.getpid()}")

    # Start health server process
    health_process = multiprocessing.Process(target=health_server_process)
    health_process.start()

    # Start fibonacci server process
    fibonacci_process = multiprocessing.Process(target=fibonacci_server_process)
    fibonacci_process.start()

    def signal_handler(signum, frame):
        print(f"Main process received signal {signum}, shutting down all processes...")
        health_process.terminate()
        fibonacci_process.terminate()
        health_process.join()
        fibonacci_process.join()
        exit(0)

    # Register signal handlers for main process
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Monitor processes and exit if either crashes
        while health_process.is_alive() and fibonacci_process.is_alive():
            time.sleep(1)

        # If we reach here, at least one process has died
        print("One or more processes have terminated unexpectedly")

        # Terminate remaining processes
        if health_process.is_alive():
            health_process.terminate()
        if fibonacci_process.is_alive():
            fibonacci_process.terminate()

        # Wait for cleanup
        health_process.join()
        fibonacci_process.join()

        # Exit with error code
        exit(1)

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
