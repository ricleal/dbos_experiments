# Experiment 14: Handling Step Retry Exhaustion with DBOSMaxStepRetriesExceeded

## Purpose

This experiment demonstrates how to gracefully handle step failures when all retry attempts have been exhausted. Instead of letting the workflow fail, it shows how to catch the `DBOSMaxStepRetriesExceeded` exception and implement custom error handling or fallback logic.

## Problem Being Solved

In production systems, external dependencies (APIs, databases, services) can fail persistently. When a DBOS step exhausts all its retry attempts:

- **Default behavior**: The exception propagates up and fails the workflow
- **Desired behavior**: Catch the exception and handle it gracefully (log, alert, use fallback, etc.)

This pattern is essential for building resilient applications that can degrade gracefully rather than fail completely.

## Key Features

- **Exception handling**: Demonstrates catching `DBOSMaxStepRetriesExceeded`
- **Retry exhaustion**: Step fails intentionally to exhaust retries
- **Graceful degradation**: Workflow continues despite step failure
- **Logging**: Tracks retry attempts and failure handling
- **Production pattern**: Shows real-world error handling approach

## Code Structure

### `provision_step()`
A step that always fails to simulate a persistent external service failure:

```python
@DBOS.step(retries_allowed=True)
def provision_step():
    DBOS.logger.info(
        f"Step: Starting provision_step {DBOS.step_status.current_attempt + 1} of {DBOS.step_status.max_attempts}"
    )
    sleep(1)  # Simulate work
    raise ValueError("Simulated failure in provision_step")
```

**Behavior:**
- Logs each retry attempt (1 of 3, 2 of 3, 3 of 3)
- Sleeps 1 second to simulate external API call
- Always raises `ValueError` to trigger retry
- After 3 attempts (default), DBOS raises `DBOSMaxStepRetriesExceeded`

### `provision_workflow()`
A workflow that catches the exception and continues execution:

```python
@DBOS.workflow()
def provision_workflow() -> bool:
    DBOS.logger.info("Workflow: Starting")
    
    try:
        provision_step()
    except DBOSMaxStepRetriesExceeded:
        DBOS.logger.error("Workflow: Caught max retries exceeded exception")
        # Could implement fallback logic here:
        # - Use cached data
        # - Return partial results
        # - Send alert to monitoring system
        # - Set workflow status flag
    
    DBOS.logger.info("Workflow: Finishing")
    return True
```

**Behavior:**
- Attempts to call the failing step
- Catches `DBOSMaxStepRetriesExceeded` when retries are exhausted
- Logs the error and continues execution
- Returns `True` indicating the workflow completed (despite the step failure)

## Expected Output

```
DBOS system database URL: postgresql://trustle:***@localhost:5432/test_dbos_sys?sslmode=disable
DBOS application database URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
Database engine parameters: {'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True, 'connect_args': {'connect_timeout': 10}}
[    INFO] (dbos:_dbos.py:370) Initializing DBOS (v2.1.0)
[    INFO] (dbos:_dbos.py:445) Executor ID: local_executer
[    INFO] (dbos:_dbos.py:446) Application version: local_v0
[ WARNING] (dbos:_dbos.py:486) Failed to start admin server: [Errno 98] Address already in use
[    INFO] (dbos:_dbos.py:496) No workflows to recover from application version local_v0
[    INFO] (dbos:_dbos.py:548) DBOS launched!
To view and manage workflows, connect to DBOS Conductor at:https://console.dbos.dev/self-host?appname=dbos-starter
[    INFO] (dbos:ex1.py:23) Workflow: Starting
[   DEBUG] (dbos:_core.py:1161) Running step, id: 1, name: provision_step
[    INFO] (dbos:ex1.py:13) Step: Starting provision_step 1 of 3
[ WARNING] (dbos:_core.py:1099) Step being automatically retried (attempt 1 of 3)
Traceback (most recent call last):
  File ".../dbos/_outcome.py", line 137, in _retry
    return func()
           ^^^^^^
  File ".../exp14/ex1.py", line 18, in provision_step
    raise ValueError("Simulated failure in provision_step")
ValueError: Simulated failure in provision_step
[    INFO] (dbos:ex1.py:13) Step: Starting provision_step 2 of 3
[ WARNING] (dbos:_core.py:1099) Step being automatically retried (attempt 2 of 3)
Traceback (most recent call last):
  File ".../dbos/_outcome.py", line 137, in _retry
    return func()
           ^^^^^^
  File ".../exp14/ex1.py", line 18, in provision_step
    raise ValueError("Simulated failure in provision_step")
ValueError: Simulated failure in provision_step
[    INFO] (dbos:ex1.py:13) Step: Starting provision_step 3 of 3
[ WARNING] (dbos:_core.py:1099) Step being automatically retried (attempt 3 of 3)
Traceback (most recent call last):
  File ".../dbos/_outcome.py", line 137, in _retry
    return func()
           ^^^^^^
  File ".../exp14/ex1.py", line 18, in provision_step
    raise ValueError("Simulated failure in provision_step")
ValueError: Simulated failure in provision_step
[   ERROR] (dbos:ex1.py:29) Workflow: Caught max retries exceeded exception
[    INFO] (dbos:ex1.py:31) Workflow: Finishing
[    INFO] (dbos:ex1.py:51) Main: Workflow output: True
```

**Key observations from the output:**

1. **Three retry attempts**: The step executes exactly 3 times (default `max_attempts`)
2. **Retry warnings**: DBOS logs "Step being automatically retried" for attempts 1 and 2
3. **Full tracebacks**: Each failure shows the complete stack trace with the `ValueError`
4. **Exception caught**: After attempt 3 fails, the workflow catches `DBOSMaxStepRetriesExceeded`
5. **Workflow continues**: Despite the step failure, the workflow logs "Finishing" and returns `True`
6. **Timing**: Each retry waits ~1 second (the `sleep(1)` in the step) plus exponential backoff
7. **Success indicator**: `Main: Workflow output: True` shows the workflow completed successfully

## Flow Diagram

```
provision_workflow()
    |
    ├─> provision_step()
    |       ├─> Attempt 1: FAIL (sleep 1s)
    |       ├─> Attempt 2: FAIL (sleep 1s)
    |       └─> Attempt 3: FAIL (sleep 1s)
    |       └─> Raise DBOSMaxStepRetriesExceeded
    |
    ├─> Catch DBOSMaxStepRetriesExceeded
    |       └─> Log error message
    |
    └─> Continue workflow execution
            └─> Return True
```

## Use Cases

### 1. Provisioning Resources
```python
try:
    provision_cloud_resource()
except DBOSMaxStepRetriesExceeded:
    DBOS.logger.error("Cloud provisioning failed after retries")
    send_alert_to_ops_team()
    use_fallback_resource()
```

### 2. External API Calls
```python
try:
    fetch_user_data_from_api()
except DBOSMaxStepRetriesExceeded:
    DBOS.logger.warning("API unavailable, using cached data")
    return get_cached_user_data()
```

### 3. Payment Processing
```python
try:
    process_payment()
except DBOSMaxStepRetriesExceeded:
    DBOS.logger.error("Payment processing failed")
    mark_order_as_pending()
    notify_customer_service()
```

### 4. Data Validation
```python
try:
    validate_external_data_source()
except DBOSMaxStepRetriesExceeded:
    DBOS.logger.warning("Validation service down, skipping checks")
    proceed_with_unvalidated_data()
```

## Configuration Options

You can customize retry behavior in the step decorator:

```python
@DBOS.step(
    retries_allowed=True,
    max_attempts=5,              # Number of retry attempts (default: 3)
    interval_seconds=2.0,        # Initial delay between retries (default: 1.0)
    backoff_rate=2.0             # Exponential backoff multiplier (default: 2.0)
)
def provision_step():
    # Your step logic
    pass
```

**Retry Schedule Example:**
- Attempt 1: immediate
- Attempt 2: after 2 seconds
- Attempt 3: after 4 seconds (2 × 2.0)
- Attempt 4: after 8 seconds (4 × 2.0)
- Attempt 5: after 16 seconds (8 × 2.0)

## Usage

```bash
# Run the experiment
python exp14/ex1.py
```

## Prerequisites

- PostgreSQL database running on `localhost:5432`
- Database: `test` with user `trustle:trustle`
- Python dependencies: `pip install dbos`

## Environment Variables

```bash
export DBOS_DATABASE_URL="postgresql://trustle:trustle@localhost:5432/test?sslmode=disable"
```

## Learning Points

1. **Exception handling**: How to catch `DBOSMaxStepRetriesExceeded` in workflows
2. **Graceful degradation**: Workflows can continue despite step failures
3. **Retry awareness**: Use `DBOS.step_status` to track retry attempts
4. **Production patterns**: Real-world error handling strategies
5. **Resilience design**: Building fault-tolerant applications
6. **Monitoring integration**: Where to add alerting and observability
7. **Fallback strategies**: Implementing alternative paths when services fail

## Best Practices

### ✅ DO:
- Catch `DBOSMaxStepRetriesExceeded` for expected failures
- Log detailed error information for debugging
- Implement meaningful fallback logic
- Set up alerts for retry exhaustion
- Track metrics on retry failures
- Use appropriate retry configuration for your use case

### ❌ DON'T:
- Silently swallow exceptions without logging
- Use empty except blocks
- Retry indefinitely without limits
- Ignore persistent failures
- Skip monitoring/alerting setup
- Use the same retry config for all operations

## Comparison with Other Approaches

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **Catch exception** (this experiment) | Graceful degradation, custom logic | Requires explicit handling | Expected failures |
| **Let workflow fail** | Simple, clear failure signal | No graceful degradation | Critical operations |
| **Increase retries** | More chances to succeed | Longer wait times | Transient failures |
| **Circuit breaker** | Prevents cascade failures | More complex implementation | Distributed systems |

## Related Patterns

- **Circuit Breaker**: Temporarily stop calling failing services
- **Fallback**: Use alternative data sources or services
- **Timeout**: Limit how long to wait for responses
- **Bulkhead**: Isolate failures to prevent system-wide impact
- **Retry with Jitter**: Add randomness to retry delays

## Future Enhancements

Potential improvements to explore:
- Implement circuit breaker pattern
- Add metrics collection for retry patterns
- Create reusable error handling utilities
- Test with real external services
- Implement progressive backoff strategies
- Add dead letter queue for failed operations

## Related Experiments

- **exp13**: Workflow recovery and step retries
- **exp15**: Performance analysis of step operations
