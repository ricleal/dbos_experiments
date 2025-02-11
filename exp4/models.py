from typing import List

from sqlalchemy import DateTime, Enum, ForeignKeyConstraint, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import uuid

class Base(DeclarativeBase):
    pass


class Accesses(Base):
    __tablename__ = 'accesses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='accesses_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))

    access_requests: Mapped[List['AccessRequests']] = relationship('AccessRequests', back_populates='access')


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

    access_requests: Mapped[List['AccessRequests']] = relationship('AccessRequests', back_populates='user')


class AccessRequests(Base):
    __tablename__ = 'access_requests'
    __table_args__ = (
        ForeignKeyConstraint(['access_id'], ['accesses.id'], name='access_requests_access_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='access_requests_user_id_fkey'),
        PrimaryKeyConstraint('id', name='access_requests_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(Enum('requested', 'approved', 'rejected', 'canceled', name='status'), server_default=text("'requested'::status"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))

    access: Mapped['Accesses'] = relationship('Accesses', back_populates='access_requests')
    user: Mapped['Users'] = relationship('Users', back_populates='access_requests')
