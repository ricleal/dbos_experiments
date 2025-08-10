# Experiment 9

## Summary

This experiment demonstrates a comprehensive DBOS-based Fibonacci calculator with multiple client-server architectures, showcasing different approaches to distributed computing, workflow management, and client-server communication patterns in DBOS.

## Files Description

### Server Implementations

- **`server.py`** - Single-process DBOS server:
  - Simple Fibonacci calculation with step-based workflow
  - Single queue with worker concurrency of 1
  - Graceful shutdown with signal handling
  - Process ID tracking and duration measurement
  - Basic workflow execution model

- **`server2.py`** - Multi-process DBOS server with health monitoring:
  - **Separate Health Server**: Independent health check endpoint on port 8080
  - **Workflow Processing**: Dedicated Fibonacci calculation process
  - **Process Isolation**: Better fault tolerance and resource management
  - **Dual Architecture**: Health monitoring separate from computation
  - **Enhanced Monitoring**: Process-level health checks and status reporting

- **`server3.py`** - Advanced server implementation (details would need inspection)

### Client Implementation

- **`client.py`** - Asynchronous DBOS client:
  - **DBOSClient Integration**: Uses DBOS client library for remote workflow execution
  - **Async/Await Pattern**: Handles multiple concurrent workflow requests
  - **Workflow Handle Management**: Tracks and waits for workflow completion
  - **Real-time Results**: Displays results as workflows complete
  - **Queue Integration**: Enqueues workflows to specific queues on remote servers
  - **Error Handling**: Comprehensive error handling for network and workflow failures

### Experimental Examples

- **`ex1.py`** - Class-based workflow experiment (with known limitations):
  - Demonstrates issues with class instantiation across process boundaries
  - Shows why stateful classes don't work well in DBOS workflow recovery
  - Educational example of what **doesn't** work in distributed DBOS

- **`ex2.py`** - Additional experimental implementation

- **`ex3.py`** - Further experimental variations

- **`ex4.py`** - More experimental approaches

- **`ex5.py`** - Final experimental implementation

### Documentation and Assets

- **`image.png`** - Architecture diagram showing the system design

- **`README.md`** - This comprehensive documentation

## Architecture Patterns Demonstrated

### Single Process Architecture (server.py)
- **Simplicity**: Single process handles all operations
- **Direct Processing**: Immediate workflow execution
- **Resource Efficiency**: Minimal overhead
- **Limited Scalability**: Single point of failure

### Multi-Process Architecture (server2.py)
- **Process Separation**: Health monitoring separate from computation
- **Fault Tolerance**: Health server continues even if workflow process fails
- **Scalability**: Independent scaling of different components
- **Monitoring**: Dedicated health check endpoints
- **Resource Isolation**: Better resource management between services

### Client-Server Communication
- **Remote Workflow Execution**: Client triggers workflows on remote DBOS servers
- **Asynchronous Processing**: Non-blocking workflow submission and result retrieval
- **Queue-based Distribution**: Work distribution through named queues
- **Result Streaming**: Real-time result delivery as computations complete

## Key Features Demonstrated

### Workflow Management
- **Step-based Execution**: Breaking down computation into recoverable steps
- **Duration Tracking**: Performance monitoring for each calculation
- **Error Recovery**: Automatic retry and recovery mechanisms
- **State Persistence**: Workflow state survives process restarts

### Client Patterns
- **Async Programming**: Modern async/await patterns for client applications
- **Workflow Handles**: Managing references to remote workflow executions
- **Result Aggregation**: Collecting and processing results from multiple workflows
- **Connection Management**: Proper database connection handling in client applications

### Operational Aspects
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
- **Process Monitoring**: PID tracking for debugging and monitoring
- **Health Checks**: Dedicated endpoints for service health monitoring
- **Logging Integration**: Comprehensive logging throughout the system

## Use Cases

This experiment demonstrates patterns suitable for:
- **Distributed Computing**: CPU-intensive tasks distributed across multiple processes
- **Microservices**: Service separation with health monitoring
- **Batch Processing**: Large-scale computational workloads
- **Real-time Systems**: Systems requiring immediate feedback on long-running operations
