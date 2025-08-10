# Experiment 2

## Summary

This experiment demonstrates a standalone DBOS application that fetches user data from an external API (randomuser.me) and processes it in bulk using DBOS workflows and queues. It showcases data integration patterns, chunked processing, and error handling with observability features.

## Files Description

### Core Application Files

- **`integration.py`** - Main integration script containing:
  - Data fetching from randomuser.me API with local caching
  - Chunked processing workflow that handles large datasets (5000 users)
  - Queue-based concurrent processing with batch inserts (10 users per batch)
  - Error handling with database logging
  - OpenTelemetry tracing integration
  - Structured JSON logging
  - Demonstrates nested workflow pattern (workflow calling another workflow)

- **`models.py`** - SQLAlchemy database models:
  - `Base` - SQLAlchemy declarative base class
  - `Errors` - Error tracking table with JSONB message storage
  - `RandomUsers` - Comprehensive user data model with 30+ fields including:
    - Personal information (name, gender, date of birth)
    - Location data (address, coordinates, timezone)
    - Contact information (email, phone, cell)
    - Authentication data (username, password hashes)
    - Profile pictures and identification numbers

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration file for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

### Data Files

- **`data/`** - Directory containing cached API response data:
  - `data.json` - Full dataset from randomuser.me API
  - `data.json.20` - Subset with 20 users (for testing)
  - `data.json.200` - Subset with 200 users (for testing)
  - `data.json.1000` - Subset with 1000 users (for testing)
  - `data.json.5000` - Subset with 5000 users (for performance testing)

### Database Migration Files

- **`migrations/`** - Alembic database migration directory with standard structure

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
