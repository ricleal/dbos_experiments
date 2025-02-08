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
            """create table if not exists tasks (
                id uuid primary key default gen_random_uuid(),
                title text null,
                data jsonb not null,
                created_at timestamp not null default now()
            );"""
        )
    )


def downgrade() -> None:
    op.execute(sa.text("drop table if exists errors"))
    op.execute(sa.text("drop table if exists tasks"))
