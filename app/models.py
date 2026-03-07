from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Float,
    ForeignKey, Integer, String, JSON, TypeDecorator
)
from sqlalchemy.orm import DeclarativeBase, relationship


class TZDateTime(TypeDecorator):
    """DateTime that always returns timezone-aware UTC datetimes.

    Works with both PostgreSQL (TIMESTAMP WITH TIME ZONE, natively tz-aware)
    and SQLite (stores as naive string; tzinfo is added on read).
    """
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    pass


class Cat(Base):
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    reference_weight_kg = Column(Float, nullable=True)
    photo_path = Column(String, nullable=True)
    created_at = Column(TZDateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    visits = relationship("Visit", back_populates="cat")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=True, index=True)
    identified_by = Column(String, nullable=True)  # 'auto' or 'manual'
    started_at = Column(TZDateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(TZDateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    created_at = Column(TZDateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    cat = relationship("Cat", back_populates="visits")


class CleaningCycle(Base):
    __tablename__ = "cleaning_cycles"

    id = Column(Integer, primary_key=True)
    started_at = Column(TZDateTime(timezone=True), nullable=False)
    ended_at = Column(TZDateTime(timezone=True), nullable=True)


class DeviceSnapshot(Base):
    __tablename__ = "device_snapshots"

    id = Column(Integer, primary_key=True)
    recorded_at = Column(TZDateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    raw_dps = Column(JSON, nullable=False)


class SettingsHistory(Base):
    __tablename__ = "settings_history"

    id = Column(Integer, primary_key=True)
    dp = Column(String, nullable=False)
    value = Column(String, nullable=False)  # store as string, parse on read
    changed_at = Column(TZDateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)