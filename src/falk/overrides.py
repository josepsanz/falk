"""Manual boost overrides: force a device on/off for a duration, beating the plan.

A boost is a single ``DeviceOverride`` row per switch carrying a target state and
an expiry. The ``apply`` reconciler honours it while it is active and resumes the
price plan once it expires.
"""

from __future__ import annotations

import datetime
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from falk.config import load_config
from falk.db import session_factory
from falk.models.devices import TuyaSwitch
from falk.models.planning import DeviceOverride
from falk.planning.devices import CONTROLLABLE_TYPES

_DURATION_PATTERN = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?$")


class DeviceNotFoundError(ValueError):
    """Raised when a boost targets a device that is not configured/stored."""


def utc_now() -> datetime.datetime:
    """Return the current time as a naive UTC datetime (matches stored columns)."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def parse_duration(text: str) -> datetime.timedelta:
    """Parse a compact duration like ``2h30m``, ``90m`` or ``1h``.

    Raises:
        ValueError: If the text is empty or not in the ``<h>h<m>m`` form.
    """
    match = _DURATION_PATTERN.fullmatch(text.strip())
    if match is None or match.group(0) == "":
        raise ValueError(f"invalid duration: {text!r} (use e.g. 2h30m, 90m, 1h)")

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    if hours == 0 and minutes == 0:
        raise ValueError(f"duration must be greater than zero: {text!r}")

    return datetime.timedelta(hours=hours, minutes=minutes)


def _resolve_switch(session: Session, identifier: str) -> TuyaSwitch | None:
    """Find a controllable switch by configured name or Tuya id."""
    tuya_id = identifier
    for device in load_config().get("devices", []):
        if device.get("type") not in CONTROLLABLE_TYPES:
            continue
        if identifier in (device.get("name"), device.get("id")):
            tuya_id = device["id"]
            break
    return session.scalar(select(TuyaSwitch).where(TuyaSwitch.tuya_id == tuya_id))


def active_override(
    session: Session, switch_id: int, now_utc: datetime.datetime
) -> DeviceOverride | None:
    """Return the device's override if one is currently active, else None."""
    return session.scalar(
        select(DeviceOverride).where(
            DeviceOverride.switch_id == switch_id,
            DeviceOverride.until_utc > now_utc,
        )
    )


def set_boost(
    identifier: str,
    *,
    desired_on: bool,
    duration: datetime.timedelta,
    now_utc: datetime.datetime | None = None,
) -> datetime.datetime:
    """Create or replace a boost for one device.

    Args:
        identifier: Device name or Tuya id.
        desired_on: State to force while the boost is active.
        duration: How long the boost lasts from now.
        now_utc: Override for the current time (testing).

    Returns:
        The UTC instant the boost expires.

    Raises:
        DeviceNotFoundError: If no controllable device matches ``identifier``.
    """
    session_maker = session_factory()
    with session_maker() as session:
        switch = _resolve_switch(session, identifier)
        if switch is None:
            raise DeviceNotFoundError(identifier)
        until_utc = set_boost_for_switch(
            session,
            switch.id,
            desired_on=desired_on,
            duration=duration,
            now_utc=now_utc,
        )
        session.commit()

    return until_utc


def clear_boost(identifier: str) -> bool:
    """Remove any boost for one device.

    Returns:
        True if a boost was removed, False if there was none.

    Raises:
        DeviceNotFoundError: If no controllable device matches ``identifier``.
    """
    session_maker = session_factory()
    with session_maker() as session:
        switch = _resolve_switch(session, identifier)
        if switch is None:
            raise DeviceNotFoundError(identifier)
        cleared = clear_boost_for_switch(session, switch.id)
        session.commit()

    return cleared


def set_boost_for_switch(
    session: Session,
    switch_id: int,
    *,
    desired_on: bool,
    duration: datetime.timedelta,
    now_utc: datetime.datetime | None = None,
) -> datetime.datetime:
    """Create or replace a boost for a switch by id (caller commits the session).

    Returns:
        The UTC instant the boost expires.
    """
    now_utc = now_utc or utc_now()
    until_utc = now_utc + duration

    override = session.scalar(
        select(DeviceOverride).where(DeviceOverride.switch_id == switch_id)
    )
    if override is None:
        session.add(
            DeviceOverride(
                switch_id=switch_id,
                desired_state=desired_on,
                until_utc=until_utc,
            )
        )
    else:
        override.desired_state = desired_on
        override.until_utc = until_utc

    return until_utc


def clear_boost_for_switch(session: Session, switch_id: int) -> bool:
    """Remove any boost for a switch by id (caller commits the session).

    Returns:
        True if a boost was removed, False if there was none.
    """
    deleted = (
        session.query(DeviceOverride)
        .filter(DeviceOverride.switch_id == switch_id)
        .delete(synchronize_session=False)
    )
    return bool(deleted)
