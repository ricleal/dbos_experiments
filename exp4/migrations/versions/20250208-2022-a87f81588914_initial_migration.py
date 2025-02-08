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
            "create type status as enum ('requested', 'approved', 'rejected', 'canceled')"
        )
    )
    op.execute(
        sa.text(
            """create table if not exists users (
                       id uuid primary key default gen_random_uuid(), 
                       name text not null, email text not null unique, 
                       created_at timestamp not null default now(), 
                       updated_at timestamp not null default now())"""
        )
    )
    op.execute(
        sa.text(
            """create table if not exists accesses (
                       id uuid primary key default gen_random_uuid(), 
                       user_id uuid not null references users (id), 
                       status status not null default 'requested', 
                       created_at timestamp not null default now(), 
                       updated_at timestamp not null default now())"""
        )
    )
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
            """insert into users (id, name, email) values
    (
        '00000000-00000000-00000000-00000001',
        'Alice',
        'alice@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000002',
        'Bob',
        'bob@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000003',
        'Charlie',
        'charlie@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000004',
        'David',
        'david@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000005',
        'Eve',
        'eve@ex.co'
    )"""
        )
    )
    op.execute(
        sa.text(
            """insert into accesses (user_id, status)
    values ('00000000-00000000-00000000-00000001', 'requested'),
        ('00000000-00000000-00000000-00000002', 'approved'),
        ('00000000-00000000-00000000-00000003', 'rejected'),
        ('00000000-00000000-00000000-00000004', 'canceled')"""
        )
    )


def downgrade() -> None:
    op.execute(sa.text("drop table if exists accesses"))
    op.execute(sa.text("drop table if exists users"))
    op.execute(sa.text("drop table if exists errors"))
    op.execute(sa.text("drop type if exists status"))
