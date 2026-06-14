"""SQLAlchemy ORM model for the per-device price-driven on/off schedule."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DeviceSchedule(Base):
    """Planned on/off state for one switch at one hour.

    A row is the desired state for ``switch_id`` during the hour starting at
    ``datetime_utc``. The plan is computed from ESIOS prices the day before and
    later reconciled against the real device state by the ``apply`` job.
    """

    __tablename__ = "device_schedule"

    __table_args__ = (
        UniqueConstraint(
            "switch_id", "datetime_utc", name="uq_device_schedule_switch_dt"
        ),
        Index("ix_device_schedule_switch_dt", "switch_id", "datetime_utc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    switch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("smart_switch.id", ondelete="CASCADE"),
        nullable=False,
    )
    datetime_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Hour the plan applies to, in UTC",
    )
    desired_state: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Planned state for the hour: True=on, False=off",
    )
    price_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="ESIOS price for the hour in €/kWh (kept for auditing/display)",
    )
    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Strategy that produced this row, e.g. cheapest_hours",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )


class DeviceOverride(Base):
    """A temporary manual boost that wins over the price plan until it expires.

    At most one override exists per switch (the unique constraint). The
    ``apply`` job forces the device to ``desired_state`` while ``until_utc`` is
    in the future, then resumes following the plan.
    """

    __tablename__ = "device_override"

    __table_args__ = (
        UniqueConstraint("switch_id", name="uq_device_override_switch"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    switch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("smart_switch.id", ondelete="CASCADE"),
        nullable=False,
    )
    desired_state: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="State to force while active: True=on, False=off",
    )
    until_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="UTC instant the boost expires",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )
