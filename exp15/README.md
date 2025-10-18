# Experiment 15: DBOS Payload Size Performance Analysis

## Purpose

This experiment measures the performance impact of different payload sizes in DBOS steps and compares two approaches:
1. **Multiple small step calls** - Calling a step multiple times with incrementally larger payloads
2. **Single batched step call** - Calling a step once that processes all payloads internally

The goal is to understand the overhead of DBOS step serialization, deserialization, and database storage as payload sizes increase from 1 byte to 1 MB.

## Experiment Design

### Approach 1: Multiple Step Calls (`size_workflow`)

Calls the `size_step()` function 7 times with increasing payload sizes:
- Iteration 1: 10^0 = 1 byte
- Iteration 2: 10^1 = 10 bytes
- Iteration 3: 10^2 = 100 bytes
- Iteration 4: 10^3 = 1,000 bytes (1 KB)
- Iteration 5: 10^4 = 10,000 bytes (10 KB)
- Iteration 6: 10^5 = 100,000 bytes (100 KB)
- Iteration 7: 10^6 = 1,000,000 bytes (1 MB)

**Total payload**: 1,111,111 bytes across 7 separate step calls

### Approach 2: Single Batched Step (`batch_size_workflow`)

Calls `batch_size_step()` once, which internally generates all 7 payloads and returns them concatenated.

**Total payload**: 1,111,111 bytes in 1 step call

## Key Observations

### Performance Results

```
Workflow: Starting
Workflow: Iteration 1/7
Step: Size step with payload size 1 bytes
Workflow: Payload size is 1 bytes, took 55.41 ms
Workflow: Iteration 2/7
Step: Size step with payload size 10 bytes
Workflow: Payload size is 10 bytes, took 21.63 ms
Workflow: Iteration 3/7
Step: Size step with payload size 100 bytes
Workflow: Payload size is 100 bytes, took 21.71 ms
Workflow: Iteration 4/7
Step: Size step with payload size 1000 bytes
Workflow: Payload size is 1000 bytes, took 21.81 ms
Workflow: Iteration 5/7
Step: Size step with payload size 10000 bytes
Workflow: Payload size is 10000 bytes, took 23.87 ms
Workflow: Iteration 6/7
Step: Size step with payload size 100000 bytes
Workflow: Payload size is 100000 bytes, took 35.45 ms
Workflow: Iteration 7/7
Step: Size step with payload size 1000000 bytes
Workflow: Payload size is 1000000 bytes, took 120.46 ms
Workflow: Completed successfully in 300.35 ms
----------------------------------------------------
Workflow: Starting
Step: Batch size step iteration 1/7
Step: Batch size step iteration 2/7
Step: Batch size step iteration 3/7
Step: Batch size step iteration 4/7
Step: Batch size step iteration 5/7
Step: Batch size step iteration 6/7
Step: Batch size step iteration 7/7
Workflow: Payload size is 1111111 bytes, took 157.82 ms
Main: Workflow output: True
```

### Analysis

| Approach | Total Time | Number of Steps | Overhead per Step |
|----------|-----------|-----------------|-------------------|
| Multiple small steps | **300.35 ms** | 7 | ~42.9 ms average |
| Single batched step | **157.82 ms** | 1 | N/A |

**Key Findings:**

1. **First step overhead**: The first step call takes ~55ms, likely due to initialization overhead
2. **Small payload consistency**: Steps with payloads 1-1000 bytes take ~21-24ms consistently
3. **Scaling behavior**: Performance degrades as payload size increases:
   - 100 KB: 35.45 ms
   - 1 MB: 120.46 ms
4. **Batching advantage**: Single batched step is **~47% faster** (157ms vs 300ms)
   - Eliminates 6 step serialization/deserialization cycles
   - Reduces database writes from 7 to 1
   - Avoids repeated DBOS framework overhead

### Performance Breakdown

```
Step Size       | Time (ms) | Delta from Previous
----------------|-----------|--------------------
1 byte          | 55.41     | baseline (includes init)
10 bytes        | 21.63     | -33.78 ms (steady state)
100 bytes       | 21.71     | +0.08 ms
1 KB            | 21.81     | +0.10 ms
10 KB           | 23.87     | +2.06 ms
100 KB          | 35.45     | +11.58 ms
1 MB            | 120.46    | +85.01 ms (non-linear growth)
```

## Performance Implications

### When to Use Multiple Steps
- **Better granularity**: Individual step recovery and retry
- **Better observability**: Track progress of each payload size
- **Memory efficiency**: Process data incrementally
- **Acceptable for small payloads** (< 10 KB): Overhead is minimal (~21-24ms per step)

### When to Use Batched Steps
- **Large payloads**: Reduces serialization overhead significantly
- **High throughput requirements**: 47% faster for same total data
- **Atomic operations**: All-or-nothing processing
- **Simple workflows**: When granular recovery isn't needed

## Code Structure

### `size_step(payload_size: int) -> bytes`
- Generates random bytes of size 10^payload_size
- Returns the payload
- Logs the payload size

### `size_workflow() -> bool`
- Calls `size_step()` 7 times with increasing sizes
- Measures and logs time for each step call
- Validates payload sizes
- Returns total execution time

### `batch_size_step(iterations: int) -> bytes`
- Generates all 7 payloads internally
- Concatenates them into a single return value
- Logs progress for each iteration

### `batch_size_workflow() -> bool`
- Calls `batch_size_step()` once with all iterations
- Measures total time
- Returns execution time

## Usage

```bash
# Run the experiment
python exp15/ex1.py
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

1. **DBOS step overhead**: ~21-24ms baseline per step for small payloads
2. **Serialization cost**: Grows non-linearly with payload size
3. **Database I/O impact**: Each step write adds overhead
4. **Batching benefits**: Significant performance gain for high-volume workflows
5. **Design trade-offs**: Granularity vs. performance
6. **Scaling behavior**: 1 MB payload takes 5.5x longer than 100 KB
7. **First call penalty**: Initial step has 2.5x overhead (~55ms vs ~21ms)

## Recommendations

- **Small data (< 10 KB)**: Use multiple steps for better observability
- **Medium data (10-100 KB)**: Balance between granularity and performance
- **Large data (> 100 KB)**: Consider batching or streaming approaches
- **High-throughput**: Batch processing can save ~47% execution time
- **Critical workflows**: Multiple steps provide better recovery granularity

## Future Experiments

Potential areas to explore:
- Compression impact on payload serialization
- Streaming large payloads through multiple steps
- Impact of concurrent step execution
- Database storage costs for large payloads
- Memory usage patterns for different approaches
