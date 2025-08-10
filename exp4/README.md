# Experiment 4

## Summary

This experiment demonstrates a comprehensive DBOS web application featuring real-time communication, scheduled workflows, and an interactive web interface. It showcases an access request management system with WebSocket integration, multiple queues, and real-time notifications.

## Files Description

### Core Application Files

- **`main.py`** - Full-featured FastAPI application with DBOS integration containing:
  - **WebSocket Support**: Real-time data updates to connected clients
  - **Scheduled Workflows**: Automated data refresh every 5 seconds using cron-style scheduling
  - **Multiple Queues**: Separate queues for Slack, email, and request processing
  - **Access Management System**: Complete workflow for requesting and approving access
  - **Real-time Notifications**: WebSocket-based notifications for approval/rejection
  - **Static File Serving**: Serves static assets and HTML templates
  - **API Endpoints**:
    - `GET /` - Main web interface
    - `POST /api/request/{user_id}/{access_id}` - Submit access requests
    - `POST /api/approve` - Approve/reject access requests
    - `WebSocket /ws/data` - Real-time data streaming

- **`models.py`** - Complex SQLAlchemy database schema:
  - `Base` - SQLAlchemy declarative base class
  - `Users` - User management with unique email constraints
  - `Accesses` - Access definitions and descriptions
  - `AccessRequests` - Junction table linking users to access with status tracking
  - `Errors` - Error logging with JSONB message storage
  - Full relationship mapping between entities

### Web Interface Files

- **`templates/index.html`** - Interactive web dashboard featuring:
  - **Real-time Data Table**: Auto-refreshing access requests display
  - **Action Buttons**: Approve/reject functionality with dynamic state
  - **Status-based Styling**: Color-coded rows based on request status
  - **Notification System**: Real-time toast notifications with icons
  - **Form Interface**: User-friendly access request submission
  - **Responsive Design**: Bootstrap-based responsive layout
  - **WebSocket Integration**: Live data updates without page refresh
  - **Sortable Tables**: Client-side sorting by columns

- **`static/`** - Directory for static assets (CSS, JS, images)

### Configuration Files

- **`__init__.py`** - Python package initialization file

- **`dbos-config.yaml`** - DBOS configuration for database and application settings

- **`envrc-template`** - Environment variables template for direnv integration

### Database Migration Files

- **`migrations/`** - Alembic database migration directory

## Key Features Demonstrated

- **Real-time Communication**: WebSocket-based live updates
- **Scheduled Workflows**: Automated background tasks with cron scheduling
- **Multi-queue Architecture**: Separate processing queues for different notification types
- **Interactive Web UI**: Full-featured dashboard with real-time updates
- **Access Management**: Complete workflow from request to approval/rejection
- **Error Handling**: Comprehensive error tracking and logging
- **Notification System**: Multi-channel notifications (Slack, Email simulation)

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
