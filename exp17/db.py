"""
Database operations for the ELT pipeline.

This module provides SQLite database operations including:
- Database and table creation
- Connected integrations seeding and querying
- User insertion and querying with duplicate handling
"""

import json
import sqlite3
from typing import List, Optional
from uuid import NAMESPACE_DNS, UUID, uuid5

from data import ConnectedIntegration, User

# ============================================================================
# Database Setup Functions
# ============================================================================


def create_database(db_path: str = "data.db", truncate: bool = False) -> None:
    """Create the SQLite database and tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file
        truncate: If True, drop and recreate the tables
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if truncate:
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS connected_integrations")

    # Create connected_integrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connected_integrations (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_data TEXT NOT NULL
        )
    """)

    # Create users table (staging)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            connected_integration_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at DATETIME DEFAULT(datetime('subsec')),
            PRIMARY KEY (id, workflow_id, created_at)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================================
# Connected Integrations Functions
# ============================================================================


def seed_connected_integrations(
    db_path: str = "data.db", num_orgs: int = 3, integrations_per_org: int = 2
) -> List[ConnectedIntegration]:
    """Seed the connected_integrations table with sample data.

    Args:
        db_path: Path to the SQLite database file
        num_orgs: Number of organizations to create
        integrations_per_org: Number of integrations per organization

    Returns:
        List of created ConnectedIntegration objects
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    integrations = []
    providers = ["google", "azure", "okta"]

    for org_idx in range(1, num_orgs + 1):
        org_id = f"org-{org_idx:03d}"

        for int_idx in range(1, integrations_per_org + 1):
            provider = providers[(org_idx + int_idx) % len(providers)]
            integration_id = uuid5(NAMESPACE_DNS, f"{org_id}:{provider}:{int_idx}")

            provider_data = {
                "permission_source_name": f"{provider}_source_{int_idx}",
                "api_endpoint": f"https://api.{provider}.com/v1",
                "last_sync": None,
            }

            integration = ConnectedIntegration(
                id=integration_id,
                organization_id=org_id,
                provider=provider,
                provider_data=provider_data,
            )
            integrations.append(integration)

            cursor.execute(
                """
                INSERT OR REPLACE INTO connected_integrations 
                (id, organization_id, provider, provider_data) 
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(integration.id),
                    integration.organization_id,
                    integration.provider,
                    json.dumps(integration.provider_data),
                ),
            )

    conn.commit()
    conn.close()

    return integrations


def get_all_connected_integrations(
    db_path: str = "data.db",
) -> List[ConnectedIntegration]:
    """Retrieve all connected integrations from the database.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        List of ConnectedIntegration objects
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, organization_id, provider, provider_data FROM connected_integrations"
    )
    rows = cursor.fetchall()

    conn.close()

    return [
        ConnectedIntegration(
            id=UUID(row[0]),
            organization_id=row[1],
            provider=row[2],
            provider_data=json.loads(row[3]),
        )
        for row in rows
    ]


# ============================================================================
# User Functions
# ============================================================================


def insert_users_batch(
    user_list: List[User],
    workflow_id: str,
    db_path: str = "data.db",
) -> None:
    """Insert a batch of User records into the database.

    Args:
        user_list: List of User objects to insert
        workflow_id: Workflow ID to associate with all records
        db_path: Path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    records = [
        (
            str(user.id),
            workflow_id,
            user.external_id,
            user.organization_id,
            str(user.connected_integration_id),
            user.name,
            user.email,
        )
        for user in user_list
    ]

    cursor.executemany(
        """
        INSERT INTO users 
        (id, workflow_id, external_id, organization_id, connected_integration_id, name, email) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    conn.commit()
    conn.close()


def get_user_count(
    db_path: str = "data.db",
    organization_id: Optional[str] = None,
    connected_integration_id: Optional[str] = None,
) -> int:
    """Get the count of users, optionally filtered by org/integration.

    Args:
        db_path: Path to the SQLite database file
        organization_id: Optional filter by organization
        connected_integration_id: Optional filter by integration

    Returns:
        Count of users
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM users WHERE 1=1"
    params = []

    if organization_id:
        query += " AND organization_id = ?"
        params.append(organization_id)

    if connected_integration_id:
        query += " AND connected_integration_id = ?"
        params.append(str(connected_integration_id))

    cursor.execute(query, params)
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_unique_user_count(
    db_path: str = "data.db",
    workflow_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    connected_integration_id: Optional[str] = None,
) -> int:
    """Get count of unique users (handling duplicates from retries).

    Uses window function to select only the most recent created_at for each
    (id, workflow_id) pair, handling both step retries and workflow recoveries.

    Args:
        db_path: Path to the SQLite database file
        workflow_id: Optional filter by workflow
        organization_id: Optional filter by organization
        connected_integration_id: Optional filter by integration

    Returns:
        Count of unique users
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        WITH ranked_users AS (
            SELECT 
                id,
                workflow_id,
                organization_id,
                connected_integration_id,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY id, workflow_id
                    ORDER BY created_at DESC
                ) as rn
            FROM users
            WHERE 1=1
    """

    params = []

    if workflow_id:
        query += " AND workflow_id = ?"
        params.append(workflow_id)

    if organization_id:
        query += " AND organization_id = ?"
        params.append(organization_id)

    if connected_integration_id:
        query += " AND connected_integration_id = ?"
        params.append(str(connected_integration_id))

    query += """
        )
        SELECT COUNT(*)
        FROM ranked_users
        WHERE rn = 1
    """

    cursor.execute(query, params)
    count = cursor.fetchone()[0]

    conn.close()
    return count
