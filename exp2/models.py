from typing import Optional

from sqlalchemy import DateTime, Double, Integer, PrimaryKeyConstraint, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime
import uuid

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


class RandomUsers(Base):
    __tablename__ = 'random_users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='random_users_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    gender: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    street_number: Mapped[Optional[int]] = mapped_column(Integer)
    street_name: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(255))
    postcode: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]] = mapped_column(Double(53))
    longitude: Mapped[Optional[float]] = mapped_column(Double(53))
    timezone_offset: Mapped[Optional[str]] = mapped_column(String(255))
    timezone_description: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    uuid: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255))
    password: Mapped[Optional[str]] = mapped_column(String(255))
    salt: Mapped[Optional[str]] = mapped_column(String(255))
    md5: Mapped[Optional[str]] = mapped_column(String(255))
    sha1: Mapped[Optional[str]] = mapped_column(String(255))
    sha256: Mapped[Optional[str]] = mapped_column(String(255))
    date_of_birth: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    registered_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    phone: Mapped[Optional[str]] = mapped_column(String(255))
    cell: Mapped[Optional[str]] = mapped_column(String(255))
    id_name: Mapped[Optional[str]] = mapped_column(String(255))
    id_value: Mapped[Optional[str]] = mapped_column(String(255))
    picture_large: Mapped[Optional[str]] = mapped_column(String(255))
    picture_medium: Mapped[Optional[str]] = mapped_column(String(255))
    picture_thumbnail: Mapped[Optional[str]] = mapped_column(String(255))
    nat: Mapped[Optional[str]] = mapped_column(String(255))
