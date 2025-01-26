# dbos_experiments

My DBOS experiments

## End points

Submit a workflow:

```json
❯ http localhost:8000/submit
{
    "event": "e04867aa-77a3-4a06-8f5e-893790d037bc",
    "wf_status": "WorkflowStatus(workflow_id='e04867aa-77a3-4a06-8f5e-893790d037bc', status='PENDING', name='process_tasks', class_name=None, config_name=None, queue_name=None, authenticated_user=None, assumed_role=None, authenticated_roles=None, recovery_attempts=0)",
    "workflow_id": "e04867aa-77a3-4a06-8f5e-893790d037bc"
}
```

View the errors:

```json
❯ http localhost:8000/errors
{
    "0b25342f-9d33-427e-8a33-da14f0dff9cc": "Task failed: <dbos._core.WorkflowHandlePolling object at 0x71a8645a2e40>::(psycopg.errors.ForeignKeyViolation) insert or update on table \"accesses\" violates foreign key constraint \"accesses_user_id_fkey\"\nDETAIL:  Key (user_id)=(00000000-0000-0000-0000-000000000000) is not present in table \"users\".\n[SQL: INSERT INTO accesses (user_id, status) VALUES (%(user_id)s::UUID, %(status)s) RETURNING accesses.id]\n[parameters: {'user_id': '00000000-0000-0000-0000-000000000000', 'status': 'requested'}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
    "83e426db-0cdf-481a-b49d-e27aa38665de": "Task failed: <dbos._core.WorkflowHandlePolling object at 0x7b37e1be38c0>::(psycopg.errors.ForeignKeyViolation) insert or update on table \"accesses\" violates foreign key constraint \"accesses_user_id_fkey\"\nDETAIL:  Key (user_id)=(00000000-0000-0000-0000-000000000000) is not present in table \"users\".\n[SQL: INSERT INTO accesses (user_id, status) VALUES (%(user_id)s::UUID, %(status)s) RETURNING accesses.id]\n[parameters: {'user_id': '00000000-0000-0000-0000-000000000000', 'status': 'requested'}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
    "938de96c-d334-48b8-b96c-01f699635068": "Task failed: <dbos._core.WorkflowHandlePolling object at 0x704d97b56660>::(psycopg.errors.ForeignKeyViolation) insert or update on table \"accesses\" violates foreign key constraint \"accesses_user_id_fkey\"\nDETAIL:  Key (user_id)=(00000000-0000-0000-0000-000000000000) is not present in table \"users\".\n[SQL: INSERT INTO accesses (user_id, status) VALUES (%(user_id)s::UUID, %(status)s) RETURNING accesses.id]\n[parameters: {'user_id': '00000000-0000-0000-0000-000000000000', 'status': 'requested'}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)"
}
```

## Instructions

```bash

## Start de DB
docker-compose up

## Stop de DB
docker-compose down

## Connect to the DB
pgcli

## Run SQL script
psql -f sql/m0001.sql

## Run the code
fastapi dev main.py

## Generate SQLAlchemy models from the DB
sqlacodegen --generator declarative --options nojoined  --outfile ./exp/models.py $POSTGRES_URL

```