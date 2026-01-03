"""
ELT Pipeline Server with Health Check

This server runs DBOS workflows with a health check endpoint.
The health check runs in a separate process while DBOS.launch() runs in the main thread.

Architecture:
- Main process: Runs DBOS.launch() and keeps workflows executing
- Health check process: HTTP server on port 8080 for health monitoring
- DuckDB (OLAP): Stores raw untreated data (staging and CDC tables)
- SQLite (OLTP): Stores final treated and unique data (latest and integrations tables)
"""

import json
import multiprocessing
import os
import signal
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from db import (
    create_database,
    get_all_connected_integrations,
    seed_connected_integrations,
)
from dbos import DBOS, DBOSConfig

# Import all workflows to register them with DBOS
# These imports are necessary even if not directly used, as they register the workflows
from elt import *  # noqa: F403,F401


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint"""

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            health_data = {
                "status": "healthy",
                "service": "elt-pipeline-server",
                "timestamp": time.time(),
                "pid": os.getpid(),
                "ppid": os.getppid(),
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_HEAD(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()


def health_server_process(parent_pid):
    """Run the health server in a separate process

    Args:
        parent_pid: PID of parent process to monitor
    """
    print(
        f"Health server starting with PID: {os.getpid()}, monitoring parent PID: {parent_pid}"
    )

    def signal_handler(signum, frame):
        print(f"Health server received signal {signum}, shutting down...")
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Allow port reuse to prevent "Address already in use" errors
    server = HTTPServer(("localhost", 8080), HealthHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Health server running on http://localhost:8080/health")

    def check_parent():
        """Monitor parent process and exit if it dies"""
        while True:
            time.sleep(1)
            try:
                # Check if parent process is still alive
                # os.kill with signal 0 doesn't kill, just checks if process exists
                os.kill(parent_pid, 0)
            except OSError:
                # Parent process is dead
                # print(
                #     f"Parent process {parent_pid} is dead, shutting down health server..."
                # )
                os._exit(0)

    # Start parent monitor thread
    monitor_thread = threading.Thread(target=check_parent, daemon=True)
    monitor_thread.start()

    server.serve_forever()


def initialize_database():
    """Initialize DuckDB (OLAP) and SQLite (OLTP) databases and seed data if needed"""
    sqlite_path = "data.db"
    duckdb_path = "data_olap.db"
    print("Initializing databases:")
    print(f"  - SQLite (OLTP): {sqlite_path}")
    print(f"  - DuckDB (OLAP): {duckdb_path}")

    create_database(sqlite_path=sqlite_path, duckdb_path=duckdb_path, truncate=False)

    # Seed connected integrations (only if not already seeded)
    existing_integrations = get_all_connected_integrations(db_path=sqlite_path)
    if not existing_integrations:
        print("Seeding connected integrations")
        integrations = seed_connected_integrations(
            db_path=sqlite_path, num_orgs=3, integrations_per_org=2
        )
        print(f"Seeded {len(integrations)} connected integrations")
    else:
        print(f"Found {len(existing_integrations)} existing connected integrations")


def main():
    """Main server process - runs DBOS and health check"""
    print(f"Main server process starting with PID: {os.getpid()}")

    # Configure DBOS
    config: DBOSConfig = {
        "name": "elt-pipeline",
        "database_url": os.getenv(
            "DBOS_DATABASE_URL",
            "postgresql://postgres:dbos@localhost:5432/test?connect_timeout=10",
        ),
        "log_level": "DEBUG",
    }
    DBOS(config=config)

    # Initialize database
    initialize_database()

    # Start health server process - pass parent PID for monitoring
    current_pid = os.getpid()
    health_process = multiprocessing.Process(
        target=health_server_process, args=(current_pid,), daemon=True
    )
    health_process.start()
    print(f"Health process started with PID: {health_process.pid}")

    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print(f"Main process received signal {signum}, shutting down gracefully...")

        # Terminate health process
        if health_process.is_alive():
            health_process.terminate()
            health_process.join(timeout=5)

        print("Shutting down DBOS...")
        DBOS.destroy()
        exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # Launch DBOS - this blocks and runs workflows
    print("Launching DBOS...")
    print(f"DBOS app version: {DBOS.application_version}")
    DBOS.launch()

    # Keep the main thread running to process workflows
    print("DBOS launched successfully. Server is ready to process workflows.")
    print("Press Ctrl+C to shut down.")

    try:
        # Block forever while DBOS processes workflows
        threading.Event().wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
