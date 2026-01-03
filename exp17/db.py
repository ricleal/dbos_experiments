"""
Database operations for the ELT pipeline.

This module provides database operations for a hybrid DuckDB + SQLite architecture:
- DuckDB (OLAP): users_staging and users_cdc tables (raw untreated data)
- SQLite (OLTP): users_latest and connected_integrations tables (final treated data)

Operations include:
- Database and table creation
- Connected integrations seeding and querying
- User insertion and querying with duplicate handling
- CDC (Change Data Capture) operations
"""

import hashlib
import json
import sqlite3
from typing import List, Optional
from uuid import NAMESPACE_DNS, UUID, uuid5

import duckdb
from data import ConnectedIntegration, User

# ============================================================================
# Helper Functions
# ============================================================================


def compute_content_hash(name: str, email: str) -> str:
    """Compute a hash digest of user content fields.

    This hash is used for efficient CDC change detection. When any of the
    included fields change, the hash will change, making it easy to detect
    updates without comparing individual fields.

    Args:
        name: User's name
        email: User's email

    Returns:
        Hexadecimal hash digest (MD5, 32 characters)
    """
    # Combine fields with a delimiter to avoid collision issues
    # e.g., "John:Smith" vs "JohnS:mith" produce different hashes
    content = f"{name}:{email}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ============================================================================
# Database Setup Functions
# ============================================================================


def create_database(
    sqlite_path: str = "data.db",
    duckdb_path: str = "data_olap.db",
    truncate: bool = False,
) -> None:
    """Create the databases and tables if they don't exist.

    DuckDB (OLAP) stores:
    - users_staging: Raw data from API with duplicates
    - users_cdc: Change data capture records

    SQLite (OLTP) stores:
    - users_latest: Current state - deduplicated, final data
    - connected_integrations: Integration metadata

    Args:
        sqlite_path: Path to the SQLite database file (OLTP)
        duckdb_path: Path to the DuckDB database file (OLAP)
        truncate: If True, drop and recreate the tables
    """
    # Create DuckDB connection for OLAP (staging and CDC)
    duck_conn = duckdb.connect(duckdb_path)

    # Create SQLite connection for OLTP (latest and integrations)
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    if truncate:
        # DuckDB tables
        duck_conn.execute("DROP TABLE IF EXISTS users_staging")
        duck_conn.execute("DROP TABLE IF EXISTS users_cdc")

        # SQLite tables
        sqlite_cursor.execute("DROP TABLE IF EXISTS users_latest")
        sqlite_cursor.execute("DROP TABLE IF EXISTS connected_integrations")

    # Create connected_integrations table in SQLite
    sqlite_cursor.execute("""
        CREATE TABLE IF NOT EXISTS connected_integrations (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_data TEXT NOT NULL
        )
    """)

    # Create users_staging table in DuckDB (raw data from API with duplicates)
    duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS users_staging (
            id VARCHAR NOT NULL,
            workflow_id VARCHAR NOT NULL,
            external_id VARCHAR NOT NULL,
            organization_id VARCHAR NOT NULL,
            connected_integration_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            content_hash VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, created_at)
        )
    """)

    # Create users_cdc table in DuckDB (change data capture)
    duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS users_cdc (
            id VARCHAR NOT NULL,
            workflow_id VARCHAR NOT NULL,
            external_id VARCHAR NOT NULL,
            organization_id VARCHAR NOT NULL,
            connected_integration_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            content_hash VARCHAR NOT NULL,
            change_type VARCHAR NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, organization_id, connected_integration_id, workflow_id, detected_at)
        )
    """)

    # Create users_latest table in SQLite (current state - deduplicated)
    sqlite_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_latest (
            id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            connected_integration_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            last_updated DATETIME DEFAULT(datetime('subsec')),
            PRIMARY KEY (id, organization_id, connected_integration_id)
        )
    """)

    sqlite_conn.commit()
    sqlite_conn.close()
    duck_conn.close()


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
    duckdb_path: str = "data_olap.db",
) -> None:
    """Insert a batch of User records into the DuckDB staging table.

    Args:
        user_list: List of User objects to insert
        workflow_id: Workflow ID to associate with all records
        duckdb_path: Path to DuckDB database file (OLAP)
    """
    conn = duckdb.connect(duckdb_path)

    records = [
        (
            str(user.id),
            workflow_id,
            user.external_id,
            user.organization_id,
            str(user.connected_integration_id),
            user.name,
            user.email,
            compute_content_hash(user.name, user.email),  # Add content hash
        )
        for user in user_list
    ]

    conn.executemany(
        """
        INSERT INTO users_staging 
        (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, content_hash) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    conn.close()


def get_user_count(
    table_name: str = "users_staging",
    organization_id: Optional[str] = None,
    connected_integration_id: Optional[str] = None,
    sqlite_path: str = "data.db",
    duckdb_path: str = "data_olap.db",
) -> int:
    """Get the count of users from a specific table, optionally filtered by org/integration.

    Uses DuckDB for users_staging and users_cdc tables (OLAP).
    Uses SQLite for users_latest table (OLTP).

    Args:
        table_name: Name of the table to query (users_staging, users_latest, users_cdc)
        organization_id: Optional filter by organization
        connected_integration_id: Optional filter by integration
        sqlite_path: Path to SQLite database file (OLTP)
        duckdb_path: Path to DuckDB database file (OLAP)

    Returns:
        Count of users
    """
    # Determine which database to use based on table name
    if table_name in ["users_staging", "users_cdc"]:
        conn = duckdb.connect(duckdb_path)
    else:  # users_latest
        conn = sqlite3.connect(sqlite_path)

    query = f"SELECT COUNT(*) FROM {table_name} WHERE 1=1"
    params = []

    if organization_id:
        query += " AND organization_id = ?"
        params.append(organization_id)

    if connected_integration_id:
        query += " AND connected_integration_id = ?"
        params.append(str(connected_integration_id))

    if table_name in ["users_staging", "users_cdc"]:
        result = conn.execute(query, params).fetchone()
        count = result[0] if result else 0
    else:
        cursor = conn.cursor()
        cursor.execute(query, params)
        count = cursor.fetchone()[0]

    conn.close()
    return count


def get_unique_user_count(
    duckdb_path: str = "data_olap.db",
    workflow_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    connected_integration_id: Optional[str] = None,
) -> int:
    """Get count of unique users from DuckDB staging (handling duplicates from retries).

    Uses window function to select only the most recent created_at for each
    (id, workflow_id) pair, handling both step retries and workflow recoveries.

    Args:
        duckdb_path: Path to DuckDB database file (OLAP)
        workflow_id: Optional filter by workflow
        organization_id: Optional filter by organization
        connected_integration_id: Optional filter by integration

    Returns:
        Count of unique users
    """
    conn = duckdb.connect(duckdb_path)

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

    result = conn.execute(query, params).fetchone()
    count = result[0] if result else 0

    conn.close()
    return count


# ============================================================================
# CDC (Change Data Capture) Functions
# ============================================================================


def detect_and_populate_cdc(
    workflow_id: str,
    organization_id: str,
    connected_integration_id: UUID,
    sqlite_path: str = "data.db",
    duckdb_path: str = "data_olap.db",
) -> dict:
    """Detect changes between DuckDB staging and SQLite latest, populate CDC table in DuckDB.

    This function uses CONTENT HASH-BASED CHANGE DETECTION for efficiency:
    - Each record has a content_hash (MD5) computed from name + email
    - UPDATEs are detected by comparing hashes instead of individual fields
    - Benefits: Simple SQL, easy to extend with more fields, faster with many columns

    This function is IDEMPOTENT - it can be called multiple times with the same
    workflow_id without creating duplicates. It first clears any existing CDC
    records for this workflow, then detects and inserts changes.

    This ensures that if a workflow crashes and is replayed, we don't create
    duplicate CDC records.

    Args:
        workflow_id: The workflow ID for tracking
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        sqlite_path: Path to SQLite database file (OLTP)
        duckdb_path: Path to DuckDB database file (OLAP)

    Returns:
        Dictionary with counts of each change type
    """
    duck_conn = duckdb.connect(duckdb_path)
    sqlite_conn = sqlite3.connect(sqlite_path)

    # IDEMPOTENCY: Delete any existing CDC records for this workflow in DuckDB
    # This ensures replays don't create duplicates
    duck_conn.execute(
        """
        DELETE FROM users_cdc 
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    )

    # Attach SQLite database to DuckDB for cross-database queries
    duck_conn.execute(f"ATTACH '{sqlite_path}' AS sqlite_db (TYPE SQLITE)")

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
                content_hash,
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
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, content_hash, change_type)
        SELECT 
            s.id,
            ? as workflow_id,
            s.external_id,
            s.organization_id,
            s.connected_integration_id,
            s.name,
            s.email,
            s.content_hash,
            'INSERT' as change_type
        FROM staging_deduped s
        LEFT JOIN sqlite_db.users_latest l ON s.id = l.id 
            AND s.organization_id = l.organization_id 
            AND s.connected_integration_id = l.connected_integration_id
        WHERE s.rn = 1 AND l.id IS NULL
    """
    )

    duck_conn.execute(
        insert_query,
        (workflow_id, organization_id, str(connected_integration_id), workflow_id),
    )

    # Count inserted rows
    result = duck_conn.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'INSERT'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    ).fetchone()
    inserts = result[0] if result else 0

    # Detect UPDATEs: Records in both staging and latest with different content_hash
    # Using hash comparison is more efficient and extensible than comparing individual fields
    # Multi-tenant: JOIN on id, organization_id, and connected_integration_id
    update_query = (
        staging_cte
        + """
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, content_hash, change_type)
        SELECT 
            s.id,
            ? as workflow_id,
            s.external_id,
            s.organization_id,
            s.connected_integration_id,
            s.name,
            s.email,
            s.content_hash,
            'UPDATE' as change_type
        FROM staging_deduped s
        INNER JOIN sqlite_db.users_latest l ON s.id = l.id 
            AND s.organization_id = l.organization_id 
            AND s.connected_integration_id = l.connected_integration_id
        WHERE s.rn = 1 
            AND s.content_hash != l.content_hash
    """
    )

    duck_conn.execute(
        update_query,
        (workflow_id, organization_id, str(connected_integration_id), workflow_id),
    )

    # Count updated rows
    result = duck_conn.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'UPDATE'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    ).fetchone()
    updates = result[0] if result else 0

    # Detect DELETEs: Records in latest but not in current staging
    # This identifies records that were previously synced but are no longer in the source
    # Multi-tenant: JOIN on id, organization_id, and connected_integration_id
    delete_query = (
        staging_cte
        + """
        INSERT INTO users_cdc (id, workflow_id, external_id, organization_id, connected_integration_id, name, email, content_hash, change_type)
        SELECT 
            l.id,
            ? as workflow_id,
            l.external_id,
            l.organization_id,
            l.connected_integration_id,
            l.name,
            l.email,
            l.content_hash,
            'DELETE' as change_type
        FROM sqlite_db.users_latest l
        LEFT JOIN staging_deduped s ON l.id = s.id 
            AND l.organization_id = s.organization_id 
            AND l.connected_integration_id = s.connected_integration_id
            AND s.rn = 1
        WHERE l.organization_id = ?
            AND l.connected_integration_id = ?
            AND s.id IS NULL
    """
    )

    duck_conn.execute(
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
    result = duck_conn.execute(
        """
        SELECT COUNT(*) FROM users_cdc 
        WHERE workflow_id = ? 
            AND organization_id = ? 
            AND connected_integration_id = ? 
            AND change_type = 'DELETE'
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    ).fetchone()
    deletes = result[0] if result else 0

    sqlite_conn.close()
    duck_conn.close()

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
    sqlite_path: str = "data.db",
    duckdb_path: str = "data_olap.db",
) -> int:
    """Apply CDC changes from DuckDB to the SQLite latest table.

    This function reads CDC records from DuckDB (OLAP) and applies them to
    the users_latest table in SQLite (OLTP), bridging the two databases.

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
        sqlite_path: Path to SQLite database file (OLTP)
        duckdb_path: Path to DuckDB database file (OLAP)

    Returns:
        Count of records applied to latest table
    """
    # Read CDC records from DuckDB
    duck_conn = duckdb.connect(duckdb_path)

    cdc_records = duck_conn.execute(
        """
        SELECT id, external_id, organization_id, connected_integration_id, 
               name, email, content_hash, change_type
        FROM users_cdc
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
        ORDER BY detected_at
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    ).fetchall()

    duck_conn.close()

    # Apply changes to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    applied_count = 0
    deleted_count = 0

    for record in cdc_records:
        (
            rec_id,
            external_id,
            rec_org_id,
            rec_integration_id,
            name,
            email,
            content_hash,
            change_type,
        ) = record

        if change_type in ["INSERT", "UPDATE"]:
            # IDEMPOTENT: INSERT OR REPLACE ensures no duplicates
            sqlite_cursor.execute(
                """
                INSERT OR REPLACE INTO users_latest 
                (id, external_id, organization_id, connected_integration_id, 
                 name, email, content_hash, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('subsec'))
                """,
                (
                    rec_id,
                    external_id,
                    rec_org_id,
                    rec_integration_id,
                    name,
                    email,
                    content_hash,
                ),
            )
            applied_count += 1
        elif change_type == "DELETE":
            # IDEMPOTENT: DELETE removes records from latest table
            sqlite_cursor.execute(
                """
                DELETE FROM users_latest
                WHERE id = ?
                    AND organization_id = ?
                    AND connected_integration_id = ?
                """,
                (rec_id, rec_org_id, rec_integration_id),
            )
            deleted_count += 1

    total_applied = applied_count + deleted_count

    sqlite_conn.commit()
    sqlite_conn.close()

    return total_applied


def get_cdc_changes(
    workflow_id: str,
    organization_id: str,
    connected_integration_id: UUID,
    duckdb_path: str = "data_olap.db",
) -> List[dict]:
    """Get all CDC changes for a specific workflow from DuckDB.

    Args:
        workflow_id: The workflow ID
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        duckdb_path: Path to DuckDB database file (OLAP)

    Returns:
        List of dictionaries containing CDC records
    """
    conn = duckdb.connect(duckdb_path)

    rows = conn.execute(
        """
        SELECT id, external_id, organization_id, connected_integration_id, 
               name, email, content_hash, change_type, detected_at
        FROM users_cdc
        WHERE workflow_id = ?
            AND organization_id = ?
            AND connected_integration_id = ?
        ORDER BY detected_at
        """,
        (workflow_id, organization_id, str(connected_integration_id)),
    ).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "external_id": row[1],
            "organization_id": row[2],
            "connected_integration_id": row[3],
            "name": row[4],
            "email": row[5],
            "content_hash": row[6],
            "change_type": row[7],
            "detected_at": row[8],
        }
        for row in rows
    ]
