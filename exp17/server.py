"""
ELT Pipeline Server with Health Check

This server runs DBOS workflows with a health check endpoint.
The health check runs in a separate process while DBOS.launch() runs in the main thread.

Architecture:
- Main process: Runs DBOS.launch() and keeps workflows executing
- Health check process: HTTP server on port 8080 for health monitoring
"""

import json
import multiprocessing
import os
import signal
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
from elt import *  # ignore: F403,F401


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


def initialize_database():
    """Initialize SQLite database and seed data if needed"""
    db_path = "data.db"
    print(f"Initializing database at {db_path}")

    create_database(db_path=db_path, truncate=False)

    # Seed connected integrations (only if not already seeded)
    existing_integrations = get_all_connected_integrations(db_path=db_path)
    if not existing_integrations:
        print("Seeding connected integrations")
        integrations = seed_connected_integrations(
            db_path=db_path, num_orgs=3, integrations_per_org=2
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

    # Start health server process
    health_process = multiprocessing.Process(target=health_server_process, daemon=True)
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
