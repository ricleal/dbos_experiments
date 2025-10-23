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
        cursor.execute("DROP TABLE IF EXISTS users_staging")
        cursor.execute("DROP TABLE IF EXISTS users_cdc")
        cursor.execute("DROP TABLE IF EXISTS users_latest")
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

    # Create users_staging table (raw data from API with duplicates)
    # Multi-tenant: id can be duplicated across orgs/integrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_staging (
            id TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            connected_integration_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at DATETIME DEFAULT(datetime('subsec')),
            PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, created_at)
        )
    """)

    # Create users_cdc table (change data capture)
    # Multi-tenant: id can be duplicated across orgs/integrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_cdc (
            id TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            connected_integration_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            change_type TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
            detected_at DATETIME DEFAULT(datetime('subsec')),
            PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, detected_at)
        )
    """)

    # Create users_latest table (current state - deduplicated)
    # Multi-tenant: id can be duplicated across orgs/integrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_latest (
            id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            connected_integration_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            last_updated DATETIME DEFAULT(datetime('subsec')),
            PRIMARY KEY (id, organization_id, connected_integration_id)
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
    """Insert a batch of User records into the staging table.

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
        INSERT INTO users_staging 
        (id, workflow_id, external_id, organization_id, connected_integration_id, name, email) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    conn.commit()
    conn.close()


def get_user_count(
    db_path: str = "data.db",
    table_name: str = "users_staging",
    organization_id: Optional[str] = None,
    connected_integration_id: Optional[str] = None,
) -> int:
    """Get the count of users from a specific table, optionally filtered by org/integration.

    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to query (users_staging, users_latest, users_cdc)
        organization_id: Optional filter by organization
        connected_integration_id: Optional filter by integration

    Returns:
        Count of users
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f"SELECT COUNT(*) FROM {table_name} WHERE 1=1"
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
    """Get count of unique users from staging (handling duplicates from retries).

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
                    PARTITION BY id, workflow_id, organization_id, connected_integration_id
                    ORDER BY created_at DESC
                ) as rn
            FROM users_staging
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


# ============================================================================
# CDC (Change Data Capture) Functions
# ============================================================================


def detect_and_populate_cdc(
    workflow_id: str,
    organization_id: str,
    connected_integration_id: UUID,
    db_path: str = "data.db",
) -> dict:
    """Detect changes between staging and latest, populate CDC table.

    This function is IDEMPOTENT - it can be called multiple times with the same
    workflow_id without creating duplicates. It first clears any existing CDC
    records for this workflow, then detects and inserts changes.

    This ensures that if a workflow crashes and is replayed, we don't create
    duplicate CDC records.

    Args:
        workflow_id: The workflow ID for tracking
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        db_path: Path to the SQLite database file

    Returns:
        Dictionary with counts of each change type
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # IDEMPOTENCY: Delete any existing CDC records for this workflow
    # This ensures replays don't create duplicates
    cursor.execute(
        """
        DELETE FROM users_cdc 
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    )

    # First, get deduplicated staging data using window function
    staging_cte = """
        WITH staging_deduped AS (
            SELECT 
                id,
                external_id,
                organization_id,
                connected_integration_id,
                name,
                email,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY id, workflow_id, organization_id, connected_integration_id
                    ORDER BY created_at DESC
                ) as rn
            FROM users_staging
            WHERE workflow_id = ?
                AND organization_id = ?
                AND connected_integration_id = ?
        )
    """

    # Detect INSERTs: Records in staging but not in latest
    # Multi-tenant: JOIN on id, organization_id, and connected_integration_id
    insert_query = (
        staging_cte
        + """
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, change_type)
        SELECT 
            s.id,
            ? as workflow_id,
            s.external_id,
            s.organization_id,
            s.connected_integration_id,
            s.name,
            s.email,
            'INSERT' as change_type
        FROM staging_deduped s
        LEFT JOIN users_latest l ON s.id = l.id 
            AND s.organization_id = l.organization_id 
            AND s.connected_integration_id = l.connected_integration_id
        WHERE s.rn = 1 AND l.id IS NULL
    """
    )

    cursor.execute(
        insert_query,
        (workflow_id, organization_id, str(connected_integration_id), workflow_id),
    )

    # Count inserted rows
    cursor.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'INSERT'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    )
    inserts = cursor.fetchone()[0]

    # Detect UPDATEs: Records in both staging and latest with different data
    # Multi-tenant: JOIN on id, organization_id, and connected_integration_id
    update_query = (
        staging_cte
        + """
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, change_type)
        SELECT 
            s.id,
            ? as workflow_id,
            s.external_id,
            s.organization_id,
            s.connected_integration_id,
            s.name,
            s.email,
            'UPDATE' as change_type
        FROM staging_deduped s
        INNER JOIN users_latest l ON s.id = l.id 
            AND s.organization_id = l.organization_id 
            AND s.connected_integration_id = l.connected_integration_id
        WHERE s.rn = 1 
            AND (s.name != l.name OR s.email != l.email)
    """
    )

    cursor.execute(
        update_query,
        (workflow_id, organization_id, str(connected_integration_id), workflow_id),
    )

    # Count updated rows
    cursor.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'UPDATE'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    )
    updates = cursor.fetchone()[0]

    # Detect DELETEs: Records in latest but not in current staging
    # This identifies records that were previously synced but are no longer in the source
    # Multi-tenant: JOIN on id, organization_id, and connected_integration_id
    delete_query = (
        staging_cte
        + """
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, change_type)
        SELECT 
            l.id,
            ? as workflow_id,
            l.external_id,
            l.organization_id,
            l.connected_integration_id,
            l.name,
            l.email,
            'DELETE' as change_type
        FROM users_latest l
        LEFT JOIN staging_deduped s ON l.id = s.id 
            AND l.organization_id = s.organization_id 
            AND l.connected_integration_id = s.connected_integration_id
            AND s.rn = 1
        WHERE l.organization_id = ?
            AND l.connected_integration_id = ?
            AND s.id IS NULL
    """
    )

    cursor.execute(
        delete_query,
        (
            workflow_id,
            organization_id,
            str(connected_integration_id),
            workflow_id,
            organization_id,
            str(connected_integration_id),
        ),
    )

    # Count deleted rows
    cursor.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'DELETE'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    )
    deletes = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return {
        "inserts": inserts,
        "updates": updates,
        "deletes": deletes,
        "total_changes": inserts + updates + deletes,
    }


def apply_cdc_to_latest(
    workflow_id: str,
    organization_id: str,
    connected_integration_id: UUID,
    db_path: str = "data.db",
) -> int:
    """Apply CDC changes to the latest table.

    This function is IDEMPOTENT - it uses INSERT OR REPLACE which means:
    - If a record doesn't exist, it's inserted
    - If a record exists, it's updated with new values
    - Multiple calls with the same data produce the same result

    For DELETE operations, it removes records from the latest table.

    This ensures that workflow replays don't create duplicate records in users_latest.

    Args:
        workflow_id: The workflow ID for tracking
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        db_path: Path to the SQLite database file

    Returns:
        Count of records applied to latest table
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # IDEMPOTENT: INSERT OR REPLACE ensures no duplicates
    # If id exists, it replaces; if not, it inserts
    apply_query = """
        INSERT OR REPLACE INTO users_latest (id, external_id, organization_id, connected_integration_id, name, email, last_updated)
        SELECT 
            id,
            external_id,
            organization_id,
            connected_integration_id,
            name,
            email,
            datetime('subsec') as last_updated
        FROM users_cdc
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
            AND change_type IN ('INSERT', 'UPDATE')
    """

    cursor.execute(
        apply_query, (workflow_id, organization_id, str(connected_integration_id))
    )
    applied_count = cursor.rowcount

    # IDEMPOTENT: DELETE removes records from latest table
    # Multiple calls with the same data produce the same result
    delete_query = """
        DELETE FROM users_latest
        WHERE (id, organization_id, connected_integration_id) IN (
            SELECT id, organization_id, connected_integration_id
            FROM users_cdc
            WHERE workflow_id = ?
                AND organization_id = ?
                AND connected_integration_id = ?
                AND change_type = 'DELETE'
        )
    """

    cursor.execute(
        delete_query, (workflow_id, organization_id, str(connected_integration_id))
    )
    deleted_count = cursor.rowcount

    total_applied = applied_count + deleted_count

    conn.commit()
    conn.close()

    return total_applied


def get_cdc_changes(
    workflow_id: str,
    organization_id: str,
    connected_integration_id: UUID,
    db_path: str = "data.db",
) -> List[dict]:
    """Get all CDC changes for a specific workflow.

    Args:
        workflow_id: The workflow ID
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        db_path: Path to the SQLite database file

    Returns:
        List of dictionaries containing CDC records
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT id, external_id, organization_id, connected_integration_id, 
               name, email, change_type, detected_at
        FROM users_cdc
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
        ORDER BY detected_at
    """

    cursor.execute(query, (workflow_id, organization_id, str(connected_integration_id)))
    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "external_id": row[1],
            "organization_id": row[2],
            "connected_integration_id": row[3],
            "name": row[4],
            "email": row[5],
            "change_type": row[6],
            "detected_at": row[7],
        }
        for row in rows
    ]
