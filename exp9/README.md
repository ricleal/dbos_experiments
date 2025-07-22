# DBOS Experiment 9 - Fibonacci Calculator

This experiment demonstrates a DBOS-based fibonacci calculator with client-server architecture.

## Architecture

![Experiment 9 Architecture](image.png)

## Files

- `server.py` - Single-process DBOS server that processes fibonacci calculations
- `server2.py` - Multi-process DBOS server with separate health and workflow processes
- `client.py` - Client that enqueues fibonacci calculation requests
- `README.md` - This documentation file
- `image.png` - Architecture diagram

## Usage

### Single Process Server
1. Start the server:
   ```bash
   python server.py
   ```

### Multi Process Server (with Health Check)
1. Start the multi-process server:
   ```bash
   python server2.py
   ```
   This will start:
   - Health server on http://localhost:8080/health
   - Fibonacci workflow server

2. In another terminal, run the client:
   ```bash
   python client.py
   ```

The client will generate random fibonacci numbers and show results as they complete.

## Features

- Asynchronous workflow processing
- Graceful shutdown with signal handling
- Real-time result display as workflows complete
- Comprehensive logging with process information
- **Multi-process architecture** (server2.py):
  - Separate health check server for monitoring
  - Independent fibonacci workflow processing
  - Better resource isolation and fault tolerance
