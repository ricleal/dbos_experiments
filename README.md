# dbos_experiments
My DBOS experiments

## Start de DB

```bash
docker-compose up
```

## Stop de DB

```bash
docker-compose down
```

## Connect to the DB

```bash
pgcli
```

## Run SQL script

```bash
psql -f sql/m0001.sql
```

## Run the code

```bash
fastapi dev main.py
```

## Generate SQLAlchemy models from the DB

```bash
sqlacodegen --generator declarative --options nojoined  --outfile ./exp/models.py $POSTGRES_URL
```