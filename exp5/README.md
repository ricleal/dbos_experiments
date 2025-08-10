# Experiment 5

## Summary

This experiment demonstrates DBOS Cloud deployment capabilities, showcasing how to deploy a DBOS application to the cloud platform. It's similar to exp4 but configured specifically for cloud deployment with proper requirements management.

## Files Description

### Core Application Files

- **`main.py`** - FastAPI application with DBOS integration, similar to exp4 but optimized for cloud deployment

- **`models.py`** - SQLAlchemy database models for the application

- **`requirements.txt`** - **Critical file** containing exact dependency versions for cloud deployment:
  - Generated using `poetry export --without-hashes --format=requirements.txt`
  - Contains all necessary packages including DBOS, FastAPI, SQLAlchemy, and their dependencies
  - Includes database drivers (psycopg2-binary, psycopg)
  - OpenTelemetry packages for observability
  - Development tools like pgcli for database inspection
  - **Note**: DBOS Cloud only supports Python 3.11

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration file for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

- **`.gitignore`** - Git ignore file that includes DBOS Cloud credentials (.dbos/credentials)

### Web Interface Files

- **`templates/`** - Directory containing HTML templates for the web interface

- **`static/`** - Directory for static assets (CSS, JS, images)

### Database Migration Files

- **`migrations/`** - Alembic database migration directory

## DBOS Cloud Deployment

This experiment specifically demonstrates:

- **Cloud CLI Integration**: Using `@dbos-inc/dbos-cloud` npm package
- **Authentication**: Login process for DBOS Cloud platform
- **Dependency Management**: Proper requirements.txt generation for cloud deployment
- **Deployment Process**: Application deployment to DBOS Cloud infrastructure
- **Cloud URL**: Applications are deployed to `<app-name>.cloud.dbos.dev`

## Key Differences from Other Experiments

- **Requirements.txt**: Explicit dependency file required for cloud deployment
- **Python Version Constraint**: Limited to Python 3.11 for DBOS Cloud compatibility
- **Cloud Configuration**: Additional configuration for cloud deployment
- **Credential Management**: Proper .gitignore setup for cloud credentials

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

### DBOS cloud cli

Note that the DBOS Cloud only supports Python 3.11!!

```bash
npm i -g @dbos-inc/dbos-cloud@latest

dbos-cloud login

echo .dbos/credentials >> .gitignore

poetry export --without-hashes --format=requirements.txt > requirements.txt

dbos-cloud app deploy

# Go to: https://ric-dbos_experiments.cloud.dbos.dev/
```

