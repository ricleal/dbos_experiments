# Experiment 7

## Summary

This experiment demonstrates DBOS workflow resumption capabilities, state management across failures, and advanced class-based workflow patterns. It showcases how DBOS handles application recovery and maintains state consistency during interruptions.

## Files Description

### Core Application Files

- **`resume.py`** - Advanced workflow resumption demonstration featuring:
  - **DBOS Configured Instance**: Uses `@dbos.DBOS.dbos_class()` with `DBOSConfiguredInstance`
  - **State Management**: Both local and global state tracking across workflow executions
  - **Publisher Pattern**: Message publishing system with failure simulation capabilities
  - **Queue-based Processing**: Concurrent message publishing with handle management
  - **State Persistence**: Counters that survive workflow interruptions and resumptions
  - **Error Handling**: Comprehensive error logging and recovery patterns
  - **Workflow Resumption**: Demonstrates how DBOS resumes workflows after failures
  - **Instance Configuration**: Named instances with persistent state across executions

### Key Features Demonstrated

#### State Management
- **Local State**: `self.local_published_messages` - instance-level counters
- **Global State**: `global_published_messages` - application-level shared state
- **State Consistency**: How DBOS maintains state across workflow interruptions

#### Publisher Architecture
- **Named Publishers**: Each publisher instance has a unique name
- **Message Tracking**: Detailed logging of published message counts
- **Failure Simulation**: Commented code for simulating application failures
- **Queue Processing**: Messages processed through DBOS queues

#### Workflow Patterns
- **Class-based Workflows**: Using DBOS class decorators for complex state management
- **Configured Instances**: Leveraging `DBOSConfiguredInstance` for persistent configuration
- **Handle Management**: Collecting and waiting for queued task completion
- **Error Recovery**: Proper exception handling for failed tasks

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

### Database Migration Files

- **`migrations/`** - Alembic database migration directory (standard structure)

## Key Concepts Demonstrated

### Workflow Resumption
- **Failure Recovery**: How DBOS automatically resumes workflows after application crashes
- **State Preservation**: Maintaining both instance and global state across restarts
- **Idempotency**: Ensuring operations can be safely repeated without side effects

### Advanced Class Patterns
- **DBOSConfiguredInstance**: Using DBOS's configured instance pattern for stateful components
- **Instance Naming**: How named instances maintain identity across executions
- **State Isolation**: Separating instance-level state from global application state

### Error Handling & Monitoring
- **Comprehensive Logging**: Detailed JSON logging for workflow tracking
- **Error Propagation**: How errors in queued tasks are handled and reported
- **State Debugging**: Logging both local and global state for debugging workflow issues

This experiment is particularly valuable for understanding how DBOS handles complex stateful applications that need to survive failures and resume processing from the exact point of interruption.

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
