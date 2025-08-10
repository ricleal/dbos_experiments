# Experiment 1

## Summary

This experiment demonstrates a basic DBOS application with FastAPI integration, featuring workflow processing, queues, and database operations. It showcases user access management with error handling and observability through structured logging.

## Files Description

### Core Application Files

- **`main.py`** - Main application file containing:
  - FastAPI application setup with DBOS integration
  - Queue configuration with concurrency limits and rate limiting (50 functions per 30 seconds)
  - Workflow definitions for processing tasks and handling errors
  - Database transactions for storing access records and error logs
  - REST API endpoints:
    - `POST /submit` - Starts a workflow with predefined user IDs
    - `POST /batch/{count}` - Starts a batch workflow with repeated user IDs
    - `GET /errors` - Retrieves all errors from the database
  - Structured JSON logging configuration
  - Event-based workflow communication

- **`models.py`** - SQLAlchemy database models:
  - `Base` - SQLAlchemy declarative base class
  - `Errors` - Table for storing error messages as JSONB with timestamps
  - `Users` - User management table with name, email, and timestamps
  - `Accesses` - User access tracking with status enum (requested, approved, rejected, canceled)
  - Proper foreign key relationships between Users and Accesses

### Configuration Files

- **`__init__.py`** - Python package initialization file (makes the directory a Python package)

- **`dbos-config.yaml`** - DBOS configuration file specifying database connections and application settings

- **`envrc-template`** - Template for environment variables (used with direnv for automatic environment loading)

### Database Migration Files

- **`migrations/`** - Alembic database migration directory containing:
  - `alembic.ini` - Alembic configuration file
  - `env.py` - Migration environment setup
  - `README` - Alembic documentation
  - `script.py.mako` - Template for generating migration scripts
  - `versions/` - Directory containing actual migration files

### Cache Files

- **`__pycache__/`** - Python bytecode cache directory (automatically generated)

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
