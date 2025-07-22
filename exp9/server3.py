import json
import multiprocessing
import os
import signal
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from dbos import DBOS, DBOSConfig, DBOSConfiguredInstance, Queue, _utils

# Initialize DBOS with a unique executor ID
_utils.GlobalParams.executor_id = str(uuid.uuid4())

config: DBOSConfig = {
    "name": "fibonacci-server",
    "database_url": "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
}
DBOS(config=config)


Queue("my_queue", worker_concurrency=1)


@DBOS.dbos_class()
class Fibonacci(DBOSConfiguredInstance):
    def __init__(self):
        super().__init__(
            config_name=f"fibonacci-server-{_utils.GlobalParams.executor_id}"
        )

    @staticmethod
    def fibonacci(n: int) -> int:
        if n <= 1:
            return n
        return Fibonacci.fibonacci(n - 1) + Fibonacci.fibonacci(n - 2)

    @DBOS.step()
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
        result = Fibonacci.fibonacci(n)
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

    @DBOS.workflow()
    def fibonacci_workflow(self, n: int) -> Tuple[int, int, float]:
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

        result = self.calculate_fibonacci_step(n)

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

    _ = Fibonacci()  # Initialize Fibonacci instance

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
        # Wait for both processes
        health_process.join()
        fibonacci_process.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
