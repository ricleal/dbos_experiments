import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from data import User


@dataclass
class ExtendedUser:
    """Extended Data class with additional database fields."""

    id: UUID
    external_id: str
    name: str
    workflow_id: Optional[str]
    analyzed_at: Optional[datetime]
    created_at: Optional[str]


def create_database(db_path: str = "user.db", truncate: bool = False) -> None:
    """Create the SQLite database and user table if they don't exist.

    Args:
        db_path: Path to the SQLite database file
        truncate: If True, drop and recreate the table (truncates existing user)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if truncate:
        # Drop the table if it exists and truncate is True
        cursor.execute("DROP TABLE IF EXISTS users")

    # Create the users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            external_id TEXT NOT NULL,
            name TEXT NOT NULL,
            workflow_id TEXT,
            analyzed_at TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id, workflow_id, analyzed_at)
        )
    """)

    conn.commit()
    conn.close()


def insert_users_page(
    user_list: List[User],
    workflow_id: str,
    analyzed_at: datetime,
    db_path: str = "data.db",
) -> None:
    """Insert a page (batch) of User records into the database.

    Args:
        user_list: List of User objects to insert
        workflow_id: Workflow ID string to associate with all records
        analyzed_at: Datetime when the user was analyzed
        db_path: Path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Convert datetime to ISO format string for storage
    analyzed_at_str = analyzed_at.isoformat()

    # Prepare the data for insertion
    records = [
        (str(data.id), data.external_id, data.name, workflow_id, analyzed_at_str)
        for data in user_list
    ]

    # Insert multiple records (created_at will be auto-generated)
    cursor.executemany(
        "INSERT INTO users (id, external_id, name, workflow_id, analyzed_at) VALUES (?, ?, ?, ?, ?)",
        records,
    )

    conn.commit()
    conn.close()


def get_all_users(db_path: str = "data.db") -> List[ExtendedUser]:
    """Retrieve all user records from the database with extended fields."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, external_id, name, workflow_id, analyzed_at, created_at FROM users"
    )
    rows = cursor.fetchall()

    conn.close()

    # Convert to ExtendedData objects
    return [
        ExtendedUser(
            id=UUID(row[0]),
            external_id=row[1],
            name=row[2],
            workflow_id=row[3],
            analyzed_at=datetime.fromisoformat(row[4]) if row[4] else None,
            created_at=row[5],
        )
        for row in rows
    ]


def get_basic_user_data(db_path: str = "data.db") -> List[User]:
    """Retrieve all user records from the database as basic User objects."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, external_id, name FROM users")
    rows = cursor.fetchall()

    conn.close()

    # Convert back to User objects
    return [User(id=UUID(row[0]), external_id=row[1], name=row[2]) for row in rows]


def get_user_count(db_path: str = "data.db") -> int:
    """Get the total count of records in the users table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def clear_users_table(db_path: str = "data.db") -> None:
    """Clear all records from the users table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")

    conn.commit()
    conn.close()
