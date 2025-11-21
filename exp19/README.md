# Experiment 19: DBOS Class Instantiation Timing

## Purpose

This experiment tests DBOS-decorated class instantiation timing to verify behavior against DBOS documentation, specifically:

> **DBOS-decorated classes must be instantiated before `DBOS.launch()` is called.**

## What This Tests

The code intentionally violates the documented guideline by:

1. Calling `DBOS.launch()` first
2. **Then** instantiating the `URLFetcher` class (a `DBOSConfiguredInstance`)
3. Running a workflow from that late-instantiated class

## Expected Behavior

According to DBOS documentation, this should generate a warning:

```
18:32:28 [ WARNING] (dbos:_dbos.py:208) Configured instance MyFetcher of class URLFetcher was registered after DBOS was launched. This may cause errors during workflow recovery. All configured instances should be instantiated before DBOS is launched.
```

## Why This Matters

DBOS maintains a global registry of configured class instances indexed by `config_name`. During workflow recovery, DBOS needs to look up the correct class instance to resume execution. If classes are instantiated after `DBOS.launch()`, recovery may fail because the instance isn't in the registry when needed.

## The Workflow

`URLFetcher.fetch_workflows()`:
- Generates 10 fake URLs using Faker
- Fetches data for each URL (simulated with `fetch_url()` step)
- Has a 1% chance of simulating an OOM error (segfault)
- Has a 5% chance per fetch of simulating a network error

## Correct Pattern

```python
# Configure DBOS
DBOS(config=config)

# Instantiate DBOS classes BEFORE launch
url_fetcher = URLFetcher(name="MyFetcher")

# Launch DBOS
DBOS.launch()

# Use the instance
handle = DBOS.start_workflow(url_fetcher.fetch_workflows)
```

## Incorrect Pattern (What This Experiment Does)

```python
# Configure DBOS
DBOS(config=config)

# Launch DBOS
DBOS.launch()

# ❌ Instantiate AFTER launch - may cause recovery issues
url_fetcher = URLFetcher(name="MyFetcher")

# Use the instance
handle = DBOS.start_workflow(url_fetcher.fetch_workflows)
```

## Running the Experiment

```bash
poetry run python ex1.py
```

## Key Observations

- The workflow may complete successfully in normal execution
- The warning appears in logs
- Problems manifest during workflow recovery after crashes
- The OOM simulation (1% chance) can trigger recovery scenarios

## Related DBOS Concepts

- `DBOSConfiguredInstance`: Base class for DBOS-decorated classes
- `config_name`: Unique identifier for class instances in the registry
- `@DBOS.dbos_class()`: Decorator marking classes for DBOS management
- Workflow recovery: Automatic resumption of workflows after failures
