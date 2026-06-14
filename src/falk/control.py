"""Reconcile real device state against the stored plan (the ``apply`` job).

Idempotent by design: each run reads the desired state for the current hour and
only actuates a device whose real state differs. LAN calls are retried; any
device that cannot be reconciled is reported via the alert channel and does not
abort the rest of the run.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from falk.alerts import send_alert
from falk.config import load_config
from falk.db import session_factory
from falk.iot.tuya import Switch
from falk.models.devices import TuyaSwitch
from falk.models.planning import DeviceSchedule
from falk.overrides import active_override, utc_now
from falk.planning.devices import iter_controlled

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_RETRY_WAIT = wait_exponential(multiplier=1, min=1, max=10)


@retry(stop=stop_after_attempt(_MAX_ATTEMPTS), wait=_RETRY_WAIT, reraise=True)
def _read_state(switch: Switch) -> bool:
    """Read the device's current on/off state, retrying transient LAN errors."""
    return bool(switch.refresh().state)


@retry(stop=stop_after_attempt(_MAX_ATTEMPTS), wait=_RETRY_WAIT, reraise=True)
def _set_state(switch: Switch, *, desired_on: bool) -> None:
    """Drive the device to ``desired_on``, retrying transient LAN errors."""
    if desired_on:
        switch.turn_on()
    else:
        switch.turn_off()


def _resolve_desired(
    session: Session,
    switch_id: int,
    hour_utc: datetime.datetime,
    now_utc: datetime.datetime,
) -> tuple[bool, str] | None:
    """Resolve the target state for a device: active boost wins over the plan.

    Returns:
        A ``(desired_on, source)`` pair, or None when there is no plan for the
        hour and no active boost (leave the device untouched).
    """
    override = active_override(session, switch_id, now_utc)
    if override is not None:
        return override.desired_state, f"boost until {override.until_utc:%H:%M} UTC"

    plan = session.scalar(
        select(DeviceSchedule).where(
            DeviceSchedule.switch_id == switch_id,
            DeviceSchedule.datetime_utc == hour_utc,
        )
    )
    if plan is None:
        return None
    return plan.desired_state, "plan"


def _reconcile_device(
    session: Session,
    device: dict,
    hour_utc: datetime.datetime,
    now_utc: datetime.datetime,
) -> str | None:
    """Bring one device in line with its boost or plan.

    Returns:
        A human-readable failure description, or None on success/no-op.
    """
    db_switch = session.scalar(
        select(TuyaSwitch).where(TuyaSwitch.tuya_id == device["id"])
    )
    if db_switch is None:
        return f"{device['name']}: scheduled but not in the database"

    resolved = _resolve_desired(session, db_switch.id, hour_utc, now_utc)
    if resolved is None:
        # No plan for this hour (e.g. prices never arrived) and no boost: leave
        # the device as is rather than guessing, and surface it for follow-up.
        return f"{device['name']}: no plan for {hour_utc:%Y-%m-%d %H:00} UTC"
    desired_on, source = resolved

    switch = Switch(
        id=device["id"],
        name=device["name"],
        ip=device["ip"],
        local_key=device["local_key"],
        version=device["version"],
    )

    try:
        current_on = _read_state(switch)
        if current_on != desired_on:
            _set_state(switch, desired_on=desired_on)
            logger.info(
                "%s: %s -> %s (%s)",
                device["name"],
                "ON" if current_on else "OFF",
                "ON" if desired_on else "OFF",
                source,
            )
        db_switch.state = desired_on
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to reconcile %s", device["name"])
        return f"{device['name']}: control failed (see logs)"

    return None


def run_apply(now_utc: datetime.datetime | None = None) -> list[str]:
    """Reconcile every controlled device against its boost or plan.

    Args:
        now_utc: Current time. Defaults to now (UTC); the plan is looked up by
            the truncated hour and boosts by the exact instant.

    Returns:
        A list of failure descriptions (empty when everything reconciled).
    """
    now_utc = now_utc or utc_now()
    hour_utc = now_utc.replace(minute=0, second=0, microsecond=0)
    config = load_config()

    failures: list[str] = []
    session_maker = session_factory()
    with session_maker() as session:
        for device, _schedule in iter_controlled(config):
            failure = _reconcile_device(session, device, hour_utc, now_utc)
            if failure is not None:
                failures.append(failure)

    if failures:
        send_alert("⚡ Falk apply failures:\n" + "\n".join(f"• {f}" for f in failures))

    return failures
