"""SQLAlchemy ORM model for ESIOS hourly PVPC electricity price data."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Float, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EsiosPrice(Base):
    """Hourly PVPC electricity price from the ESIOS indicator 1001 feed.

    One row per hour. ``price_kwh`` is the consumer-facing price in €/kWh
    (ESIOS ``value`` / 1000).
    """

    __tablename__ = "esios_price"

    __table_args__ = (
        UniqueConstraint("datetime_utc", name="uq_esios_price_datetime_utc"),
        Index("ix_esios_price_datetime_utc", "datetime_utc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    datetime_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Hour timestamp in UTC — tz_utc",
    )
    datetime_local: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Hour timestamp in Europe/Madrid — tz_local",
    )
    price_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="PVPC price in €/kWh — value / 1000",
    )
