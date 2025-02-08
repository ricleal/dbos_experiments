# Experiment 3

## Summary

Standalone application with a database to test observability.

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
