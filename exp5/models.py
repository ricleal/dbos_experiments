import datetime
import uuid
from typing import List

from sqlalchemy import DateTime, Enum, ForeignKeyConstraint, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Errors(Base):
    __tablename__ = 'errors'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='errors_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    message: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))

    accesses: Mapped[List['Accesses']] = relationship('Accesses', back_populates='user')


class Accesses(Base):
    __tablename__ = 'accesses'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], name='accesses_user_id_fkey'),
        PrimaryKeyConstraint('id', name='accesses_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(Enum('requested', 'approved', 'rejected', 'canceled', name='status'), server_default=text("'requested'::status"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='accesses')
