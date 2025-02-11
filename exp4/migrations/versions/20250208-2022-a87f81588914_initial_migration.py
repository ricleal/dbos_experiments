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
                       description text not null,
                       created_at timestamp not null default now(), 
                       updated_at timestamp not null default now())"""
        )
    )
    op.execute(
        sa.text(
            """create table if not exists access_requests (
                       id uuid primary key default gen_random_uuid(), 
                       user_id uuid not null references users (id),
                       access_id uuid not null references accesses (id),
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
            """insert into
              users (id, name, email) values
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
            """insert into accesses (id, description) values
            (
                '00000000-00000000-00000000-00000001',
                'S3 Access'
            ),
            (
                '00000000-00000000-00000000-00000002',
                'STS Access'
            ),
            (
                '00000000-00000000-00000000-00000003',
                'Lambda Access'
            ),
            (
                '00000000-00000000-00000000-00000004',
                'EC2 Access'
            ),
            (
                '00000000-00000000-00000000-00000005',
                'RDS Access'
            )"""
        )
    )

    op.execute(
        sa.text(
            """insert into access_requests (id, user_id, access_id, status) values
            (
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000001',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000002',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000003',
                'rejected'
            ),
            (
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000004',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000005',
                '00000000-00000000-00000000-00000001',
                '00000000-00000000-00000000-00000005',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000006',
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000001',
                'canceled'
            ),
            (
                '00000000-00000000-00000000-00000007',
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000002',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000008',
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000003',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000009',
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000004',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000010',
                '00000000-00000000-00000000-00000002',
                '00000000-00000000-00000000-00000005',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000011',
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000001',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000012',
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000002',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000013',
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000003',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000014',
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000004',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000015',
                '00000000-00000000-00000000-00000003',
                '00000000-00000000-00000000-00000005',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000016',
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000001',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000017',
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000002',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000018',
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000003',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000019',
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000004',
                'requested'
            ),
            (
                '00000000-00000000-00000000-00000020',
                '00000000-00000000-00000000-00000004',
                '00000000-00000000-00000000-00000005',
                'requested'
            )"""
        )
    )


def downgrade() -> None:
    op.execute(sa.text("drop table if exists accesses"))
    op.execute(sa.text("drop table if exists users"))
    op.execute(sa.text("drop table if exists access_requests"))
    op.execute(sa.text("drop table if exists errors"))
    op.execute(sa.text("drop type if exists status"))
