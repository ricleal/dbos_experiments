# Exp24: In limbo workflows

# Error

# Terminal 1

Launch the server with:
```bash
❯ uv run python main.py    
INFO:     Started server process [2332074]
INFO:     Waiting for application startup.
16:20:49 [    INFO] (dbos:_dbos.py:379) Initializing DBOS (v2.8.0)
16:20:49 [    INFO] (dbos:_dbos.py:449) Executor ID: exp22-executor-1
16:20:49 [    INFO] (dbos:_dbos.py:450) Application version: 0.1.0
16:20:49 [    INFO] (dbos:_sys_db.py:420) Initializing DBOS system database with URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
16:20:49 [    INFO] (dbos:_sys_db.py:428) DBOS system database engine parameters: {'connect_args': {'application_name': 'dbos_transact', 'connect_timeout': 10}, 'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True}
16:20:49 [    INFO] (dbos:_dbos.py:507) No workflows to recover from application version 0.1.0
16:20:49 [    INFO] (dbos:_queue.py:195) Listening to 1 queues:
16:20:49 [    INFO] (dbos:_dbos.py:562) DBOS launched!
16:20:49 [    INFO] (dbos:_queue.py:258) Queue: example-queue
16:20:49 [    INFO] (dbos:_dbos.py:570) To view and manage workflows, connect to DBOS Conductor at: https://console.dbos.dev/self-host?appname=dbos-starter
16:20:49 ->> Application started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

# Terminal 2

Check the queue with:
```bash
❯ http localhost:8000/queue
HTTP/1.1 200 OK
content-length: 23
content-type: application/json
date: Thu, 05 Feb 2026 21:22:15 GMT
server: uvicorn

{
    "queued_workflows": []
}
```

Launch a workflow with:
```bash
❯ http localhost:8000/     
HTTP/1.1 200 OK
content-length: 627
content-type: application/json
date: Thu, 05 Feb 2026 21:22:24 GMT
server: uvicorn

{
    "status": "completed",
    "workflow_status": {
        "app_id": "",
        "app_version": "0.1.0",
        "assumed_role": null,
        "authenticated_roles": null,
        "authenticated_user": null,
        "class_name": null,
        "config_name": null,
        "created_at": 1770326545905,
        "deduplication_id": "6/5",
        "error": null,
        "executor_id": "exp22-executor-1",
        "forked_from": null,
        "input": {
            "args": [
                6,
                5
            ],
            "kwargs": {}
        },
        "name": "dbos_workflow",
        "output": null,
        "priority": 0,
        "queue_name": "example-queue",
        "queue_partition_key": null,
        "recovery_attempts": 0,
        "status": "ENQUEUED",
        "updated_at": 1770326545905,
        "workflow_deadline_epoch_ms": null,
        "workflow_id": "fe5f923f-1531-4c06-af78-f4e8f9b5b9c4",
        "workflow_timeout_ms": null
    }
}
```

# Terminal 1

Response to launching a workflow:
```
16:22:25 ->> Enqueuing workflow with sub-workflows: 6, steps per workflow: 5
INFO:     127.0.0.1:35656 - "GET / HTTP/1.1" 200 OK
16:22:26 [    INFO] (dbos:main.py:78) fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: Starting workflow
16:22:26 [    INFO] (dbos:main.py:61) 	fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1 :: Starting sub-workflow 0
16:22:26 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::1 :: 	 Step 0 - Attempt 0/3
16:22:27 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:27 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::4 :: 	 Step 1 - Attempt 0/3
16:22:27 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:27 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::7 :: 	 Step 2 - Attempt 0/3
16:22:28 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:28 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::10 :: 	 Step 3 - Attempt 0/3
```

After crash, launch the server again (2nd time):
```sh
❯ uv run python main.py
INFO:     Started server process [2332718]
INFO:     Waiting for application startup.
16:22:44 [    INFO] (dbos:_dbos.py:379) Initializing DBOS (v2.8.0)
16:22:44 [    INFO] (dbos:_dbos.py:449) Executor ID: exp22-executor-1
16:22:44 [    INFO] (dbos:_dbos.py:450) Application version: 0.1.0
16:22:44 [    INFO] (dbos:_sys_db.py:420) Initializing DBOS system database with URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
16:22:44 [    INFO] (dbos:_sys_db.py:428) DBOS system database engine parameters: {'connect_args': {'application_name': 'dbos_transact', 'connect_timeout': 10}, 'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True}
16:22:44 [    INFO] (dbos:_dbos.py:503) Recovering 2 workflows from application version 0.1.0
16:22:44 [    INFO] (dbos:_queue.py:195) Listening to 1 queues:
16:22:44 [    INFO] (dbos:_dbos.py:562) DBOS launched!
16:22:44 [    INFO] (dbos:_queue.py:258) Queue: example-queue
16:22:44 [    INFO] (dbos:_dbos.py:570) To view and manage workflows, connect to DBOS Conductor at: https://console.dbos.dev/self-host?appname=dbos-starter
16:22:44 ->> Application started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
16:22:44 [    INFO] (dbos:main.py:61) 	fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1 :: Starting sub-workflow 0
16:22:44 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:44 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:45 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:45 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::10 :: 	 Step 3 - Attempt 0/3
```

After crash, launch the server again (3rd time):
```sh
❯ uv run python main.py
INFO:     Started server process [2332821]
INFO:     Waiting for application startup.
16:22:59 [    INFO] (dbos:_dbos.py:379) Initializing DBOS (v2.8.0)
16:22:59 [    INFO] (dbos:_dbos.py:449) Executor ID: exp22-executor-1
16:22:59 [    INFO] (dbos:_dbos.py:450) Application version: 0.1.0
16:22:59 [    INFO] (dbos:_sys_db.py:420) Initializing DBOS system database with URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
16:22:59 [    INFO] (dbos:_sys_db.py:428) DBOS system database engine parameters: {'connect_args': {'application_name': 'dbos_transact', 'connect_timeout': 10}, 'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True}
16:22:59 [    INFO] (dbos:_dbos.py:503) Recovering 1 workflows from application version 0.1.0
16:22:59 [    INFO] (dbos:_queue.py:195) Listening to 1 queues:
16:22:59 [    INFO] (dbos:_queue.py:258) Queue: example-queue
16:22:59 [    INFO] (dbos:_dbos.py:562) DBOS launched!
16:22:59 [    INFO] (dbos:_dbos.py:570) To view and manage workflows, connect to DBOS Conductor at: https://console.dbos.dev/self-host?appname=dbos-starter
16:22:59 ->> Application started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
16:22:59 [    INFO] (dbos:main.py:61) 	fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1 :: Starting sub-workflow 0
16:22:59 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:59 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:59 [    INFO] (dbos:main.py:70) 	* 0: Queued workflow: fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 :: dbos_workflow:PENDING - 1
16:22:59 [    INFO] (dbos:main.py:44) 		fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1::10 :: 	 Step 3 - Attempt 0/3
```

After crash, launch the server again (4th time):
```sh
❯ uv run python main.py
INFO:     Started server process [2332954]
INFO:     Waiting for application startup.
16:23:12 [    INFO] (dbos:_dbos.py:379) Initializing DBOS (v2.8.0)
16:23:12 [    INFO] (dbos:_dbos.py:449) Executor ID: exp22-executor-1
16:23:12 [    INFO] (dbos:_dbos.py:450) Application version: 0.1.0
16:23:12 [    INFO] (dbos:_sys_db.py:420) Initializing DBOS system database with URL: postgresql://trustle:***@localhost:5432/test?sslmode=disable
16:23:12 [    INFO] (dbos:_sys_db.py:428) DBOS system database engine parameters: {'connect_args': {'application_name': 'dbos_transact', 'connect_timeout': 10}, 'pool_timeout': 30, 'max_overflow': 0, 'pool_size': 20, 'pool_pre_ping': True}
16:23:12 [    INFO] (dbos:_dbos.py:503) Recovering 1 workflows from application version 0.1.0
16:23:12 [    INFO] (dbos:_queue.py:195) Listening to 1 queues:
16:23:12 [    INFO] (dbos:_queue.py:258) Queue: example-queue
16:23:12 [    INFO] (dbos:_dbos.py:562) DBOS launched!
16:23:12 [    INFO] (dbos:_dbos.py:570) To view and manage workflows, connect to DBOS Conductor at: https://console.dbos.dev/self-host?appname=dbos-starter
16:23:12 ->> Application started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
16:23:12 [   ERROR] (dbos:_recovery.py:41) Exception encountered when recovering workflow fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1:
Traceback (most recent call last):
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_recovery.py", line 35, in startup_recovery_thread
    _recover_workflow(dbos, pending_workflow)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_recovery.py", line 23, in _recover_workflow
    return execute_workflow_by_id(dbos, workflow.workflow_uuid, True, False)
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_core.py", line 551, in execute_workflow_by_id
    return start_workflow(
        dbos,
    ...<6 lines>...
        is_dequeued=is_dequeue,
    )
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_core.py", line 649, in start_workflow
    status, should_execute = _init_workflow(
                             ~~~~~~~~~~~~~~^
        dbos,
        ^^^^^
    ...<11 lines>...
        is_dequeued_request=is_dequeued,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_core.py", line 320, in _init_workflow
    dbos._sys_db.init_workflow(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^
        status,
        ^^^^^^^
    ...<3 lines>...
        owner_xid=str(uuid.uuid4()),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 335, in wrapper
    return func(*args, **kwargs)
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 2173, in init_workflow
    self._insert_workflow_status(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        status,
        ^^^^^^^
    ...<4 lines>...
        is_dequeued_request=is_dequeued_request,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 626, in _insert_workflow_status
    raise MaxRecoveryAttemptsExceededError(
        status["workflow_uuid"], max_recovery_attempts
    )
dbos._error.MaxRecoveryAttemptsExceededError: DBOS Error 6: Workflow fe5f923f-1531-4c06-af78-f4e8f9b5b9c4-1 has exceeded its maximum of 2 execution or recovery attempts. Further attempts to execute or recover it will fail. See documentation for details: https://docs.dbos.dev/python/reference/decorators
```

# Terminal 2

Launching the workflow with the same deduplicated ID.
```sh
❯ http localhost:8000/
HTTP/1.1 200 OK
content-length: 186
content-type: application/json
date: Thu, 05 Feb 2026 21:23:23 GMT
server: uvicorn

{
    "message": "DBOS Error 12: Workflow 71c6a5a5-46a0-4271-8507-5045d82f73c7 was deduplicated due to an existing workflow in queue example-queue with deduplication ID 6/5.",
    "status": "error"
}
```

# Terminal 1

This showed an exception `dbos._error.DBOSQueueDeduplicatedError`.
```
16:23:24 ->> Enqueuing workflow with sub-workflows: 6, steps per workflow: 5
16:23:24 ->> Failed to enqueue workflow
Traceback (most recent call last):
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/psycopg/cursor.py", line 117, in execute
    raise ex.with_traceback(None)
psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "uq_workflow_status_queue_name_dedup_id"
DETAIL:  Key (queue_name, deduplication_id)=(example-queue, 6/5) already exists.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 562, in _insert_workflow_status
    results = conn.execute(cmd)
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
    return meth(
        self,
        distilled_parameters,
        execution_options or NO_OPTIONS,
    )
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/sql/elements.py", line 527, in _execute_on_connection
    return connection._execute_clauseelement(
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self, distilled_params, execution_options
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
    ret = self._execute_context(
        dialect,
    ...<8 lines>...
        cache_hit=cache_hit,
    )
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
    return self._exec_single_context(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 2363, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/psycopg/cursor.py", line 117, in execute
    raise ex.with_traceback(None)
sqlalchemy.exc.IntegrityError: (psycopg.errors.UniqueViolation) duplicate key value violates unique constraint "uq_workflow_status_queue_name_dedup_id"
DETAIL:  Key (queue_name, deduplication_id)=(example-queue, 6/5) already exists.
[SQL: INSERT INTO dbos.workflow_status (workflow_uuid, status, name, authenticated_user, assumed_role, authenticated_roles, output, error, executor_id, application_version, application_id, class_name, config_name, recovery_attempts, queue_name, workflow_timeout_ms, workflow_deadline_epoch_ms, deduplication_id, inputs, priority, queue_partition_key, owner_xid) VALUES (%(workflow_uuid)s::VARCHAR, %(status)s::VARCHAR, %(name)s::VARCHAR, %(authenticated_user)s::VARCHAR, %(assumed_role)s::VARCHAR, %(authenticated_roles)s::VARCHAR, %(output)s::VARCHAR, %(error)s::VARCHAR, %(executor_id)s::VARCHAR, %(application_version)s::VARCHAR, %(application_id)s::VARCHAR, %(class_name)s::VARCHAR, %(config_name)s::VARCHAR, %(recovery_attempts)s::BIGINT, %(queue_name)s::VARCHAR, %(workflow_timeout_ms)s::BIGINT, %(workflow_deadline_epoch_ms)s::BIGINT, %(deduplication_id)s::VARCHAR, %(inputs)s::VARCHAR, %(priority)s::INTEGER, %(queue_partition_key)s::VARCHAR, %(owner_xid)s::VARCHAR) ON CONFLICT (workflow_uuid) DO UPDATE SET updated_at = (EXTRACT(epoch FROM now()) * %(param_1)s::INTEGER), recovery_attempts = CASE WHEN (dbos.workflow_status.status != %(status_1)s::VARCHAR) THEN dbos.workflow_status.recovery_attempts + %(recovery_attempts_1)s::BIGINT ELSE dbos.workflow_status.recovery_attempts END RETURNING dbos.workflow_status.recovery_attempts, dbos.workflow_status.status, dbos.workflow_status.workflow_deadline_epoch_ms, dbos.workflow_status.name, dbos.workflow_status.class_name, dbos.workflow_status.config_name, dbos.workflow_status.queue_name, dbos.workflow_status.owner_xid]
[parameters: {'workflow_uuid': '71c6a5a5-46a0-4271-8507-5045d82f73c7', 'status': 'ENQUEUED', 'name': 'dbos_workflow', 'authenticated_user': None, 'assumed_role': None, 'authenticated_roles': None, 'output': None, 'error': None, 'executor_id': 'exp22-executor-1', 'application_version': '0.1.0', 'application_id': '', 'class_name': None, 'config_name': None, 'recovery_attempts': 0, 'queue_name': 'example-queue', 'workflow_timeout_ms': None, 'workflow_deadline_epoch_ms': None, 'deduplication_id': '6/5', 'inputs': 'gASVHQAAAAAAAAB9lCiMBGFyZ3OUSwZLBYaUjAZrd2FyZ3OUfZR1Lg==', 'priority': 0, 'queue_partition_key': None, 'owner_xid': '09bf3fbb-837a-4b3f-9662-25a51ceb4a2b', 'param_1': 1000, 'status_1': 'ENQUEUED', 'recovery_attempts_1': 0}]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/leal/git/dbos_experiments/exp24/main.py", line 95, in handle_request
    handle: WorkflowHandle = queue.enqueue(dbos_workflow, n_sub_workflows, n_steps_per_workflow)
                             ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_queue.py", line 101, in enqueue
    return start_workflow(
        dbos, func, args, kwargs, queue_name=self.name, execute_workflow=False
    )
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_core.py", line 649, in start_workflow
    status, should_execute = _init_workflow(
                             ~~~~~~~~~~~~~~^
        dbos,
        ^^^^^
    ...<11 lines>...
        is_dequeued_request=is_dequeued,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_core.py", line 320, in _init_workflow
    dbos._sys_db.init_workflow(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^
        status,
        ^^^^^^^
    ...<3 lines>...
        owner_xid=str(uuid.uuid4()),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 335, in wrapper
    return func(*args, **kwargs)
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 2173, in init_workflow
    self._insert_workflow_status(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        status,
        ^^^^^^^
    ...<4 lines>...
        is_dequeued_request=is_dequeued_request,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/leal/git/dbos_experiments/.venv/lib/python3.13/site-packages/dbos/_sys_db.py", line 568, in _insert_workflow_status
    raise DBOSQueueDeduplicatedError(
    ...<3 lines>...
    )
dbos._error.DBOSQueueDeduplicatedError: DBOS Error 12: Workflow 71c6a5a5-46a0-4271-8507-5045d82f73c7 was deduplicated due to an existing workflow in queue example-queue with deduplication ID 6/5.
```

# Terminal 2

Checking the queue. The workflow remains `PENDING`.

```sh
❯ http localhost:8000/queue
HTTP/1.1 200 OK
content-length: 586
content-type: application/json
date: Thu, 05 Feb 2026 21:25:53 GMT
server: uvicorn

{
    "queued_workflows": [
        {
            "app_id": "",
            "app_version": "0.1.0",
            "assumed_role": null,
            "authenticated_roles": null,
            "authenticated_user": null,
            "class_name": null,
            "config_name": null,
            "created_at": 1770326545905,
            "deduplication_id": "6/5",
            "error": null,
            "executor_id": "exp22-executor-1",
            "forked_from": null,
            "input": null,
            "name": "dbos_workflow",
            "output": null,
            "priority": 0,
            "queue_name": "example-queue",
            "queue_partition_key": null,
            "recovery_attempts": 2,
            "status": "PENDING",
            "updated_at": 1770326593723,
            "workflow_deadline_epoch_ms": null,
            "workflow_id": "fe5f923f-1531-4c06-af78-f4e8f9b5b9c4",
            "workflow_timeout_ms": null
        }
    ]
}
```


# Terminal 1

Pressing Ctrl+C at this moment will show the output below:
```
^CINFO:     Shutting down
INFO:     Waiting for application shutdown.
16:47:43 [    INFO] (dbos:_queue.py:229) Stopping queue manager, joining all worker threads...
16:47:44 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:45 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:46 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:47 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:48 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:49 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:50 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:51 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:52 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:53 [    INFO] (dbos:_dbos.py:617) Attempting to shut down DBOS. 1 workflows remain active. IDs: ['fe5f923f-1531-4c06-af78-f4e8f9b5b9c4']
16:47:53 [    INFO] (dbos:_dbos.py:308) DBOS successfully shut down
16:47:53 ->> Graceful shutdown complete
INFO:     Application shutdown complete.
INFO:     Finished server process [2332954]
```

After restarting the server workflow (not steps!) `max_recovery_attempts` , finaly the workflow is marked as failed:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
16:52:16 [   ERROR] (dbos:_queue.py:155) Error executing workflow fe5f923f-1531-4c06-af78-f4e8f9b5b9c4: DBOS Error 6: Workflow fe5f923f-1531-4c06-af78-f4e8f9b5b9c4 has exceeded its maximum of 2 execution or recovery attempts. Further attempts to execute or recover it will fail. See documentation for details: https://docs.dbos.dev/python/reference/decorators
INFO:     127.0.0.1:54440 - "GET /queue HTTP/1.1" 200 OK
```