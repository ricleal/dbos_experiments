# Experiment 6

## Summary

This experiment explores DBOS scope management, class-based workflows, caching patterns, application lifecycle, and Docker containerization. It demonstrates different aspects of DBOS application architecture through multiple specialized implementations.

## Files Description

### Core Application Files

- **`scope.py`** - DBOS class-based workflow demonstration:
  - `@DBOS.dbos_class()` decorator usage for class-based workflows
  - Instance-level state management within workflows
  - Step execution within class instances
  - Demonstrates how DBOS handles object scope in workflows

- **`fastapi_scope.py`** - FastAPI integration with DBOS classes:
  - Class-based workflow with instance state (`counter`)
  - Synchronous and asynchronous workflow triggers
  - FastAPI endpoints for workflow management
  - Demonstrates object lifecycle in web applications

- **`fastapi_scope_cache.py`** - Caching patterns and application lifecycle:
  - Global cache implementation (`credentials_cache`)
  - Application lifespan management with `@asynccontextmanager`
  - DBOS lifecycle hooks (`DBOS.launch()`, `DBOS.destroy()`)
  - Credential caching and reuse patterns
  - User processing workflows with cached data

- **`fastapi_scope_shutdown.py`** - Application shutdown and scheduled workflows:
  - Fibonacci calculation in steps (CPU-intensive operation)
  - Queue-based processing with 50 concurrent steps
  - Scheduled workflows (every 5 seconds)
  - Application shutdown endpoint
  - Process lifecycle management

- **`integration.py`** - Integration patterns (details would need file inspection)

- **`nested_wfs.py`** - Nested workflow patterns (details would need file inspection)

- **`scope_funcs.py`** - Scope utility functions (details would need file inspection)

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

- **`requirements.txt`** - Python dependencies for the experiment

### Docker Configuration

- **`Dockerfile`** - Container configuration for DBOS application:
  - Based on `python:3.12-slim`
  - Installs minimal dependencies: `dbos`, `fastapi`, `psycopg2-binary`, `python-json-logger`
  - Configures environment variables for PostgreSQL connection
  - Exposes port 8000 for FastAPI
  - Runs `fastapi_scope_shutdown.py` by default
  - Demonstrates containerized DBOS deployment

### Cache Files

- **`__pycache__/`** - Python bytecode cache directory

## Key Concepts Demonstrated

### DBOS Class System
- **Object Scope**: How DBOS maintains object state across workflow execution
- **Instance Management**: Creating and managing class instances within workflows
- **State Persistence**: How instance variables persist during workflow execution

### Application Lifecycle
- **Startup/Shutdown**: Proper DBOS initialization and cleanup
- **Lifespan Management**: FastAPI lifespan events integration
- **Resource Management**: Cache initialization and cleanup

### Caching Patterns
- **Global Caching**: Application-level cache for credentials and configuration
- **Scope Isolation**: How cache state interacts with workflow scope
- **Performance Optimization**: Reducing redundant operations through caching

### Containerization
- **Docker Integration**: Running DBOS applications in containers
- **Environment Configuration**: Database connection through environment variables
- **Production Deployment**: Container-ready DBOS application setup

### DBOS

```bash
dbos start
```

