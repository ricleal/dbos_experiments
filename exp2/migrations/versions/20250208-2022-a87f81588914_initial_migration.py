"""initial migration

Revision ID: a87f81588914
Revises: 
Create Date: 2025-02-08 20:22:30.618452

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a87f81588914"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """create table if not exists errors (
                       id uuid primary key default gen_random_uuid(), 
                       message jsonb not null,
                       created_at timestamp not null default now())"""
        )
    )
    op.execute(
        sa.text(
            """create table if not exists random_users (
            id uuid primary key,
            gender VARCHAR(255),
            title VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            street_number INTEGER,
            street_name VARCHAR(255),
            city VARCHAR(255),
            state VARCHAR(255),
            country VARCHAR(255),
            postcode VARCHAR(255),
            latitude double precision,
            longitude double precision,
            timezone_offset VARCHAR(255),
            timezone_description VARCHAR(255),
            email VARCHAR(255),
            uuid VARCHAR(255),
            username VARCHAR(255),
            password VARCHAR(255),
            salt VARCHAR(255),
            md5 VARCHAR(255),
            sha1 VARCHAR(255),
            sha256 VARCHAR(255),
            date_of_birth TIMESTAMP,
            age INTEGER,
            registered_at TIMESTAMP,
            phone VARCHAR(255),
            cell VARCHAR(255),
            id_name VARCHAR(255),
            id_value VARCHAR(255),
            picture_large VARCHAR(255),
            picture_medium VARCHAR(255),
            picture_thumbnail VARCHAR(255),
            nat VARCHAR(255)
        );"""
        )
    )


def downgrade() -> None:
    op.execute(sa.text("drop table if exists errors"))
    op.execute(sa.text("drop table if exists random_users"))
