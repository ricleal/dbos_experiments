# Experiment 10

## Summary

This experiment demonstrates advanced DBOS error handling, workflow recovery mechanisms, and process isolation patterns. It explores how DBOS handles different types of failures (exceptions vs OOM errors) and showcases multiprocessing integration within DBOS workflows.

## Files Description

### Core Application Files

- **`exp1.py`** - Comprehensive error handling and recovery demonstration:
  - **Error Type Analysis**: Documents how DBOS handles different error types:
    - **Step Exceptions**: Retried without replaying
    - **Step OOM**: Retried with replaying  
    - **Workflow Exceptions**: Workflow finishes early (like success)
    - **Workflow OOM**: Retried without replaying completed steps
  - **Multiprocessing Integration**: Uses Python's `multiprocessing.Process` within DBOS steps
  - **Process Isolation**: Fibonacci calculation executed in separate process for memory safety
  - **Step Retry Configuration**: Both steps configured with `retries_allowed=True`
  - **Workflow Recovery**: Configured with `max_recovery_attempts=3`
  - **Queue Management**: Handles pending workflows and workflow continuation
  - **Fixed Executor ID**: Uses constant executor and app version for consistent recovery

## Key Features Demonstrated

### Error Handling Patterns
- **Exception vs OOM Handling**: Different recovery behaviors for different error types
- **Step-level Retries**: Individual step retry configuration and status tracking
- **Workflow-level Recovery**: Workflow restart capabilities with attempt tracking
- **Error Simulation**: Commented code for simulating OOM and exception errors

### Process Isolation
- **Multiprocessing Integration**: Using `multiprocessing.Process` within DBOS steps
- **Memory Safety**: Isolating memory-intensive operations in separate processes
- **Inter-process Communication**: Using `multiprocessing.Queue` for result passing
- **Process Lifecycle**: Proper process creation, execution, and cleanup

### Workflow Continuity
- **Pending Workflow Detection**: Checking for existing workflows in queue
- **Workflow Retrieval**: Recovering and waiting for existing workflows
- **Queue State Management**: Handling workflow state across application restarts
- **Graceful Continuation**: Seamless continuation of interrupted workflows

### Advanced Configuration
- **Fixed Executor ID**: Ensuring consistent workflow recovery across restarts
- **App Version Control**: Explicit version management for workflow compatibility
- **Retry Configuration**: Fine-tuned retry settings for different failure scenarios
- **Recovery Attempts**: Configurable maximum recovery attempts

## Error Handling Documentation

The experiment includes detailed comments explaining DBOS error handling behavior:

### Step-level Errors
- **Exception**: Step retried without replaying previous operations
- **OOM (Out of Memory)**: Step retried with full replay of operations

### Workflow-level Errors  
- **Exception**: Workflow terminates early (treated as successful completion)
- **OOM**: Workflow retried without replaying successfully completed steps

### Multi-step Recovery
- **Sequential Execution**: If step 2 fails with OOM, step 1 is assumed successful
- **State Preservation**: Completed steps don't need re-execution during recovery

## Process Architecture

### Multiprocessing Pattern
- **Parent Process**: DBOS workflow execution
- **Child Process**: Isolated Fibonacci calculation
- **Communication**: Result passing through multiprocessing queues
- **Resource Management**: Automatic process cleanup and resource release

### Memory Management
- **Isolation Benefits**: Memory leaks in child processes don't affect parent
- **OOM Protection**: Child process OOM doesn't crash main application
- **Resource Limits**: Child processes can have independent resource limits

## Production Considerations

This experiment demonstrates patterns useful for:
- **Memory-intensive Operations**: Isolating memory-heavy computations
- **Fault Tolerance**: Robust error handling and recovery
- **Long-running Workflows**: Workflows that need to survive application restarts
- **Resource Management**: Preventing memory leaks and resource exhaustion

The combination of DBOS workflow management with multiprocessing provides a robust foundation for production systems requiring both reliability and performance.
