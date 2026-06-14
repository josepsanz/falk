"""Helpers to resolve which configured devices are price-controlled."""

from __future__ import annotations

from collections.abc import Iterator

from .config import ScheduleConfig

CONTROLLABLE_TYPES = frozenset({"tuya-smart-plug"})


def iter_controlled(config: dict) -> Iterator[tuple[dict, ScheduleConfig]]:
    """Yield each controllable device with its parsed, enabled schedule.

    Devices without a ``schedule`` block, with ``enabled: false`` inside it, or
    of a non-controllable type are skipped so they are never actuated.
    """
    for device in config.get("devices", []):
        if device.get("type") not in CONTROLLABLE_TYPES:
            continue
        raw_schedule = device.get("schedule")
        if not raw_schedule:
            continue
        schedule = ScheduleConfig.model_validate(raw_schedule)
        if not schedule.enabled:
            continue
        yield device, schedule
