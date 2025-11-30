# Experiment 20: DBOS Queue Concurrency Performance

## Overview

This experiment measures DBOS queue performance with different concurrency settings. It enqueues multiple workflows and tracks execution time to understand how queue concurrency parameters affect throughput.

## Queue Concurrency Parameters

```python
queue = Queue("my_queue", concurrency=10, worker_concurrency=5)
```

- **`concurrency`**: Global maximum across all DBOS processes (default: unlimited)
- **`worker_concurrency`**: Per-process maximum (default: unlimited)

The effective limit is the **minimum** of these two values when running a single process.

## Key Metrics

The experiment tracks:
- **Enqueue time**: How long it takes to submit all workflows to the queue
- **Total execution time**: Real wall-clock time from start to completion
- **Workflow delays**: Cumulative time spent in workflow steps
- **Completion order**: Which workflows finish first (using `asyncio.as_completed`)

## Running the Experiment

```bash
python exp20/main.py
```

### Adjusting Parameters

To test different configurations, modify:

```python
# Number of workflows to enqueue
n_workflows = 10

# Queue concurrency limits
queue = Queue("my_queue", concurrency=10, worker_concurrency=5)

# Per-workflow step count and delay
total_delay = sum([await fetch_url(fake.url()) for _ in range(5)])  # 5 steps
delay = 0.2  # 0.2s per step in fetch_url
```

## Performance Considerations

### Optimal Concurrency Settings

1. **CPU-bound workflows**: Set `worker_concurrency` ≈ number of CPU cores
2. **I/O-bound workflows**: Higher values (10-50+) for better throughput
3. **Rate-limited APIs**: Match concurrency to API limits to avoid throttling
4. **Resource constraints**: Lower values to control memory/connection usage

### Expected Behavior

With `n_workflows=10`, `worker_concurrency=5`, and 1 second per workflow:
- First 5 workflows execute immediately
- Remaining 5 wait in queue
- Second batch executes as first batch completes
- Total time: ~2 seconds (2 batches × 1 second)

### Taking Advantage of DBOS Queues

**Benefits:**
- **Automatic recovery**: Enqueued workflows survive process restarts
- **Persistent state**: Queue state stored in database
- **Controlled resource usage**: Prevent overwhelming downstream services
- **Fair scheduling**: FIFO order with optional priority
- **Distributed execution**: Global concurrency limits across multiple processes

**Best Practices:**
1. Use `enqueue_async` for non-blocking submission
2. Process results with `asyncio.as_completed` for real-time feedback
3. Set `worker_concurrency` based on bottleneck (CPU, I/O, or external API)
4. Monitor queue depth and adjust concurrency if workflows pile up
5. Use multiple queues to separate different types of work

## Database Requirement

Requires PostgreSQL connection. Set in config:

```python
config: DBOSConfig = {
    "name": "dbos-starter",
    "database_url": "postgresql://user:pass@localhost:5432/dbname",
}
```

## Example Output

```
All Workflows Enqueued: total_workflows=10, real_time_enqueue_elapsed=0.05s
Workflow Result (as completed): instance_id=3, total_delay=1.0s
Workflow Result (as completed): instance_id=1, total_delay=1.0s
...
All Workflows Completed: real_time_elapsed=2.1s, total_main_delay=10.0s
```

The `real_time_elapsed` shows wall-clock time while `total_main_delay` shows cumulative workflow time, demonstrating the parallelization benefit.
