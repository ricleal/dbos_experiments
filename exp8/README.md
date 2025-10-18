# Experiment 8: DBOS Workflows vs Python Multiprocessing Performance Comparison

This experiment explores the parallelization capabilities of DBOS workflows and compares them with traditional Python multiprocessing. The goal is to understand how DBOS handles CPU-intensive tasks and whether it can bypass Python's Global Interpreter Lock (GIL) limitations.

## Files

### 1. `main.py` - DBOS Async Workflows with Queues
Demonstrates DBOS workflows running CPU-intensive tasks (Fibonacci calculations) using:
- **Async workflows** with `@DBOS.workflow()` decorator
- **Queue-based concurrency** with configurable limits (`concurrency=10`, `worker_concurrency=5`)
- Process monitoring (logs PID/PPID for each workflow)

**Key Finding**: All workflows run in the **same process** (single PID), limited by Python's GIL. While DBOS provides durable execution and resilience, it doesn't create separate processes for true parallel CPU-bound workloads.

### 2. `exp_multip.py` - Standard Python Multiprocessing Baseline
Pure Python multiprocessing implementation using `Pool(10)` to compute Fibonacci numbers:
- Creates **separate processes** (different PIDs) for true parallelism
- Bypasses the GIL for CPU-intensive calculations
- Serves as a performance baseline for comparison

**Key Finding**: Shows significantly better performance for CPU-bound tasks due to actual parallel execution across multiple cores.

### 3. `hybrid_dbos_multiprocessing.py` - Hybrid Approach
Combines DBOS durability with multiprocessing performance:
- **DBOS workflows** for orchestration and fault tolerance
- **DBOS steps** that internally use `multiprocessing.Pool`
- Achieves both durable execution (DBOS) and true parallelism (multiprocessing)

**Architecture**:
```
DBOS Workflow → DBOS Step → Multiprocessing Pool → Parallel Processes
(orchestration)  (durable)    (performance)         (true parallel)
```

## Key Insights

1. **DBOS Limitation**: DBOS workflows don't create separate processes - all run in a single process, subject to GIL limitations
2. **Performance**: For CPU-intensive tasks, standard multiprocessing is faster than DBOS workflows alone
3. **Best of Both Worlds**: The hybrid approach leverages DBOS for durability/recovery while using multiprocessing for performance
4. **Use Cases**:
   - Use DBOS workflows for I/O-bound tasks, orchestration, and resilience
   - Use multiprocessing within DBOS steps for CPU-bound computations
   - The hybrid approach is ideal when you need both fault tolerance and parallel performance

## Running the Experiments

```bash
# DBOS async workflows (single process)
python exp8/main.py

# Standard multiprocessing (multiple processes, faster)
python exp8/exp_multip.py

# Hybrid DBOS + multiprocessing (durable + fast)
python exp8/hybrid_dbos_multiprocessing.py
```

All experiments log PIDs to demonstrate process creation patterns and execution timing.
