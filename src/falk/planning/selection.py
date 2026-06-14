"""Pure hour-selection strategies.

These functions take the day's prices and a policy and return the set of UTC
hours a device should be ON. They have no I/O so they are trivially testable.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from .config import ScheduleConfig


@dataclass(frozen=True, slots=True, kw_only=True)
class HourPrice:
    """One hour of ESIOS price data, carrying both UTC and local timestamps."""

    datetime_utc: datetime.datetime
    datetime_local: datetime.datetime
    price_kwh: float


class UnknownStrategyError(ValueError):
    """Raised when a schedule references a strategy that is not implemented."""


def cheapest_hours(prices: list[HourPrice], count: int) -> set[datetime.datetime]:
    """Return the UTC timestamps of the ``count`` cheapest hours of the day."""
    ranked = sorted(prices, key=lambda hour: hour.price_kwh)
    return {hour.datetime_utc for hour in ranked[:count]}


def select_on_hours(
    *, config: ScheduleConfig, prices: list[HourPrice]
) -> set[datetime.datetime]:
    """Resolve the set of UTC hours a device should be ON for the day.

    Args:
        config: The device's schedule policy.
        prices: Every priced hour of the target local day.

    Returns:
        The UTC hour timestamps where the device should be ON, including any
        ``min_guaranteed`` local hours regardless of price.

    Raises:
        UnknownStrategyError: If ``config.strategy`` is not implemented.
    """
    match config.strategy:
        case "cheapest_hours":
            chosen = cheapest_hours(prices, config.hours)
        case _:
            raise UnknownStrategyError(config.strategy)

    forced = {
        hour.datetime_utc
        for hour in prices
        if hour.datetime_local.hour in config.min_guaranteed
    }
    return chosen | forced
