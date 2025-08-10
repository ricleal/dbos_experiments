# Experiment 8

## Summary

This experiment explores parallel processing approaches in DBOS, comparing DBOS queues with traditional Python multiprocessing. It demonstrates different concurrency patterns and their performance characteristics for CPU-intensive tasks.

## Files Description

### Core Application Files

- **`main.py`** - DBOS queue-based parallel processing:
  - **DBOS Queue Configuration**: Queue with 10 concurrency and 5 worker concurrency
  - **Fibonacci Computation**: CPU-intensive task for performance testing
  - **Workflow Execution**: Parallel workflows executed through DBOS queues
  - **Process Tracking**: Detailed logging of process IDs (PID/PPID) and execution times
  - **Performance Monitoring**: Duration tracking for each workflow execution
  - **DBOS Integration**: Full DBOS lifecycle with database connection and workflow management
  - **Concurrency Control**: Managed parallelism through DBOS queue system

- **`exp_multip.py`** - Traditional Python multiprocessing baseline:
  - **Native Multiprocessing**: Uses Python's `multiprocessing.Pool` with 10 workers
  - **Fibonacci Computation**: Same CPU-intensive task for fair comparison
  - **Performance Baseline**: Demonstrates traditional parallel processing approach
  - **Process Tracking**: Similar logging for process IDs and execution times
  - **No DBOS Overhead**: Pure Python multiprocessing without database or workflow overhead

- **`hybrid_dbos_multiprocessing.py`** - Hybrid approach combining both:
  - **DBOS Steps with Multiprocessing**: DBOS workflow containing multiprocessing pool
  - **Best of Both Worlds**: DBOS workflow management with native multiprocessing performance
  - **Complex Task Distribution**: Demonstrates how to integrate existing multiprocessing code into DBOS
  - **Process Hierarchy**: Shows complex parent-child process relationships
  - **Performance Optimization**: Leverages multiprocessing for CPU-bound tasks within DBOS workflows

## Key Concepts Demonstrated

### Concurrency Patterns
- **DBOS Queues**: Managed concurrency with built-in retry, persistence, and monitoring
- **Python Multiprocessing**: Native OS-level parallelism for CPU-intensive tasks
- **Hybrid Approach**: Combining DBOS workflow management with multiprocessing performance

### Performance Comparison
- **Execution Times**: Direct comparison between DBOS queues and multiprocessing
- **Process Management**: Different approaches to process creation and management
- **Resource Utilization**: How each approach uses system resources

### Process Tracking
- **PID/PPID Logging**: Understanding process relationships in each approach
- **Execution Monitoring**: Detailed timing and performance metrics
- **Workflow Management**: How DBOS manages long-running CPU-intensive tasks

### Use Case Analysis
- **DBOS Queues**: Best for I/O-bound tasks, need persistence, retry logic, monitoring
- **Multiprocessing**: Best for CPU-bound tasks, maximum performance, no persistence needed
- **Hybrid**: Complex workflows requiring both benefits

## Performance Insights

Based on the included execution logs:
- **Traditional Multiprocessing**: Faster execution for pure CPU tasks due to direct OS process management
- **DBOS Queues**: Slightly slower but provides workflow persistence, error handling, and monitoring
- **Trade-offs**: Performance vs. reliability, observability, and workflow management capabilities

This experiment helps determine when to use DBOS queues versus traditional multiprocessing based on specific application requirements.
