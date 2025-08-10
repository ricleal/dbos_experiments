# Experiment 3

## Summary

This experiment demonstrates DBOS retry mechanisms, error handling, and observability features including OpenTelemetry metrics integration. It showcases how DBOS handles step failures and workflow recovery with comprehensive monitoring.

## Files Description

### Core Application Files

- **`integration.py`** - Main application demonstrating:
  - **Retry Mechanism**: Step with configurable retry settings (`max_attempts=1`)
  - **Error Simulation**: Deliberate failure for "task 50" to test error handling
  - **OpenTelemetry Metrics**: OTLP exporter configuration with console and HTTP endpoints
  - **Workflow Recovery**: Maximum recovery attempts set to 3
  - **Queue Processing**: Concurrent task processing with error tracking
  - **Metrics Collection**: Counter for database operations (insert_error, insert_task)
  - **Data Transformation**: Step that converts strings to uppercase with error simulation
  - **Random Data Generation**: Uses seeded random for reproducible testing

- **`models.py`** - SQLAlchemy database models:
  - `Base` - SQLAlchemy declarative base class
  - `Errors` - Error tracking table with JSONB message storage and timestamps
  - `Tasks` - Task data storage with JSONB data field and optional title

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration file for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

### Data Files

- **`data/`** - Directory containing test datasets (similar structure to exp2):
  - Various JSON files with different data sizes for testing
  - Used for performance and load testing scenarios

### Database Migration Files

- **`migrations/`** - Alembic database migration directory with standard structure

## Key Features Demonstrated

- **Retry Logic**: Steps can automatically retry on failure with configurable attempts
- **Error Handling**: Comprehensive error catching and database logging
- **Observability**: OpenTelemetry metrics with both console and OTLP exporters
- **Workflow Recovery**: Automatic workflow restart on failure
- **Queue Processing**: Concurrent task execution with error isolation

## Development

Run docker compose in the parent directory:

```bash
docker compose up
```

### Alembic

```bash
# alembic init migrations

# export ALEMBIC_CONFIG=migrations/alembic.ini

# alembic revision -m "initial migration"

alembic upgrade head

```

### Generate models from the database

```bash
# sqlacodegen --generator declarative --options nojoined  --outfile models.py $POSTGRES_URL
```

### DBOS

```bash
# Alternative to alembic upgrade head
# dbos migrate

dbos start
```

### DB

To inspect the database:

```bash
pgcli
```
