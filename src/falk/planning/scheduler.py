"""Build and persist the daily on/off plan from stored ESIOS prices."""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from falk.config import load_config
from falk.db import session_factory
from falk.models.devices import TuyaSwitch
from falk.models.planning import DeviceSchedule
from falk.models.pricing import EsiosPrice

from .config import ScheduleConfig
from .devices import iter_controlled
from .selection import HourPrice, select_on_hours

logger = logging.getLogger(__name__)


def _day_prices(session: Session, day: datetime.date) -> list[HourPrice]:
    """Load every priced hour whose local timestamp falls on ``day``."""
    start = datetime.datetime.combine(day, datetime.time())
    end = start + datetime.timedelta(days=1)
    rows = session.scalars(
        select(EsiosPrice)
        .where(EsiosPrice.datetime_local >= start, EsiosPrice.datetime_local < end)
        .order_by(EsiosPrice.datetime_local)
    ).all()
    return [
        HourPrice(
            datetime_utc=row.datetime_utc,
            datetime_local=row.datetime_local,
            price_kwh=row.price_kwh,
        )
        for row in rows
    ]


def _plan_device(
    session: Session, switch: TuyaSwitch, schedule: ScheduleConfig, prices: list[HourPrice]
) -> tuple[int, int]:
    """Replace the stored schedule for ``switch`` on the priced day.

    Returns:
        A ``(rows_written, hours_on)`` pair.
    """
    on_hours = select_on_hours(config=schedule, prices=prices)

    planned_utcs = [hour.datetime_utc for hour in prices]
    session.query(DeviceSchedule).filter(
        DeviceSchedule.switch_id == switch.id,
        DeviceSchedule.datetime_utc.in_(planned_utcs),
    ).delete(synchronize_session=False)

    session.add_all(
        DeviceSchedule(
            switch_id=switch.id,
            datetime_utc=hour.datetime_utc,
            desired_state=hour.datetime_utc in on_hours,
            price_kwh=hour.price_kwh,
            strategy=schedule.strategy,
        )
        for hour in prices
    )
    return len(prices), len(on_hours)


def build_plan(day: datetime.date | None = None) -> int:
    """Compute and store the on/off plan for every controlled device.

    Args:
        day: Local day to plan. Defaults to tomorrow, matching the ``pricing``
            job which fetches the next day's prices.

    Returns:
        Total number of schedule rows written across all devices.
    """
    day = day or (datetime.date.today() + datetime.timedelta(days=1))
    config = load_config()

    session_maker = session_factory()
    total = 0
    with session_maker() as session:
        prices = _day_prices(session, day)
        if not prices:
            logger.warning("No ESIOS prices stored for %s; nothing to plan", day)
            return 0

        for device, schedule in iter_controlled(config):
            switch = session.scalar(
                select(TuyaSwitch).where(TuyaSwitch.tuya_id == device["id"])
            )
            if switch is None:
                logger.warning(
                    "Device %s is scheduled but not in the database; skipping",
                    device["name"],
                )
                continue

            written, on_count = _plan_device(session, switch, schedule, prices)
            logger.info(
                "Planned %s: %d/%d hours ON for %s", device["name"], on_count, written, day
            )
            total += written

        session.commit()

    return total
