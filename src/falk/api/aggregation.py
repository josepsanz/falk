"""Time-series aggregation queries over the SQLite metrics tables.

All bucketing is done with SQLite ``strftime`` on the naive-local ``recorded_at``
column. Power series average the instantaneous samples; energy series derive
consumption from the cumulative Wh counters (meters) or by integrating power
over the sampling interval (plugs, which lack a cumulative counter).
"""

import datetime
from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, aliased

from falk.models.devices import EMMetric, Phase, SmartSwitch, SwitchMetric

from .schemas import Granularity, Metric, PhaseSel, TimeseriesPoint

# Assumed telemetry sampling interval, in hours, used to integrate plug power
# into energy (plugs expose no cumulative counter). The cron runs every 5 min.
_PLUG_SAMPLE_INTERVAL_HOURS = 5 / 60

_WH_PER_KWH = 1000.0

# Safety cap: refuse ranges that would produce an unreasonable number of buckets.
MAX_BUCKETS = 2000

_STRFTIME_FORMAT: dict[Granularity, str] = {
    Granularity.minute: "%Y-%m-%d %H:%M:00",
    Granularity.hour: "%Y-%m-%d %H:00:00",
    Granularity.day: "%Y-%m-%d",
    Granularity.month: "%Y-%m",
}

_DEFAULT_WINDOW: dict[Granularity, datetime.timedelta] = {
    Granularity.minute: datetime.timedelta(hours=6),
    Granularity.hour: datetime.timedelta(days=7),
    Granularity.day: datetime.timedelta(days=90),
    Granularity.month: datetime.timedelta(days=730),
}


class BucketRangeTooLargeError(ValueError):
    """Raised when a requested range would exceed :data:`MAX_BUCKETS`."""


@dataclass(frozen=True, slots=True)
class TimeRange:
    """An inclusive-start, exclusive-end naive-local time range."""

    start: datetime.datetime
    end: datetime.datetime


@dataclass(frozen=True, slots=True)
class DeviceShare:
    """A single device's latest power draw."""

    id: int
    name: str
    power: float


@dataclass(frozen=True, slots=True)
class Breakdown:
    """Latest household consumption split across devices plus the remainder."""

    total_act_power: float
    recorded_at: datetime.datetime
    devices: list[DeviceShare]
    assigned: float
    unassigned: float


def consumption_breakdown(session: Session, meter_id: int) -> Breakdown | None:
    """Split the meter's latest total power across plugs and the unassigned rest.

    The unassigned slice (total minus the sum of plug draws, clamped at zero)
    captures consumption not metered by any individual plug.
    """
    latest_meter = session.execute(
        select(EMMetric.total_act_power, EMMetric.recorded_at)
        .where(EMMetric.em_id == meter_id)
        .order_by(EMMetric.recorded_at.desc())
        .limit(1)
    ).first()
    if latest_meter is None:
        return None
    total, recorded_at = latest_meter

    # Latest metric id per switch via a correlated lookup. This uses the
    # (switch_id, recorded_at) index as one seek per switch, so it stays fast
    # as switch_metric grows (unlike a full-table window scan).
    inner = aliased(SwitchMetric)
    latest_metric_id = (
        select(inner.id)
        .where(inner.switch_id == SmartSwitch.id)
        .order_by(inner.recorded_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    rows = session.execute(
        select(SmartSwitch.id, SmartSwitch.name, SwitchMetric.power)
        .join(SwitchMetric, SwitchMetric.id == latest_metric_id)
        .where(SmartSwitch.enabled.is_(True))
        .order_by(SwitchMetric.power.desc())
    ).all()

    devices = [
        DeviceShare(id=switch_id, name=name, power=float(power))
        for switch_id, name, power in rows
    ]
    assigned = sum(device.power for device in devices)
    unassigned = max(0.0, total - assigned)
    return Breakdown(
        total_act_power=total,
        recorded_at=recorded_at,
        devices=devices,
        assigned=assigned,
        unassigned=unassigned,
    )


def resolve_range(
    granularity: Granularity,
    dt_from: datetime.datetime | None,
    dt_to: datetime.datetime | None,
    *,
    now: datetime.datetime,
) -> TimeRange:
    """Resolve the effective time range, applying per-granularity defaults.

    Args:
        granularity: Bucket size, which determines the default window.
        dt_from: Explicit start, or None to use the default window.
        dt_to: Explicit end, or None to use ``now``.
        now: Current naive-local time (injected for testability).

    Returns:
        The resolved range.

    Raises:
        BucketRangeTooLargeError: If the range yields more than MAX_BUCKETS.
    """
    end = dt_to or now
    start = dt_from or (end - _DEFAULT_WINDOW[granularity])
    if start >= end:
        return TimeRange(start=start, end=start)
    if _estimate_bucket_count(start, end, granularity) > MAX_BUCKETS:
        raise BucketRangeTooLargeError(
            f"range {start}..{end} at {granularity} granularity exceeds "
            f"{MAX_BUCKETS} buckets"
        )
    return TimeRange(start=start, end=end)


def meter_timeseries(
    session: Session,
    meter_id: int,
    *,
    metric: Metric,
    granularity: Granularity,
    phase: PhaseSel,
    time_range: TimeRange,
) -> tuple[str, list[TimeseriesPoint]]:
    """Build a meter time series. Returns the unit and the densified points."""
    if metric is Metric.power:
        rows = _meter_power_rows(session, meter_id, phase, granularity, time_range)
        unit = "W"
    else:
        rows = _meter_energy_rows(session, meter_id, phase, granularity, time_range)
        unit = "kWh"
    return unit, _densify(rows, granularity, time_range)


def plug_timeseries(
    session: Session,
    plug_id: int,
    *,
    metric: Metric,
    granularity: Granularity,
    time_range: TimeRange,
) -> tuple[str, list[TimeseriesPoint]]:
    """Build a plug time series. Returns the unit and the densified points."""
    bucket = _bucket_label(SwitchMetric.recorded_at, granularity)
    if metric is Metric.power:
        value = func.avg(SwitchMetric.power)
        unit = "W"
    else:
        # No cumulative counter: integrate average power over the window.
        value = func.sum(SwitchMetric.power) * (
            _PLUG_SAMPLE_INTERVAL_HOURS / _WH_PER_KWH
        )
        unit = "kWh"
    stmt = (
        select(bucket.label("bucket"), value.label("value"))
        .where(
            SwitchMetric.switch_id == plug_id,
            SwitchMetric.recorded_at >= time_range.start,
            SwitchMetric.recorded_at < time_range.end,
        )
        .group_by("bucket")
        .order_by("bucket")
    )
    return unit, _densify(_run(session, stmt), granularity, time_range)


def _meter_power_rows(
    session: Session,
    meter_id: int,
    phase: PhaseSel,
    granularity: Granularity,
    time_range: TimeRange,
) -> dict[str, float]:
    bucket = _bucket_label(EMMetric.recorded_at, granularity)
    if phase is PhaseSel.total:
        stmt = _meter_base(
            select(bucket.label("bucket"), func.avg(EMMetric.total_act_power)),
            meter_id,
            time_range,
        )
    else:
        stmt = _phase_base(
            select(bucket.label("bucket"), func.avg(Phase.act_power)),
            meter_id,
            phase,
            time_range,
        )
    return _run(session, stmt.group_by("bucket").order_by("bucket"))


def _meter_energy_rows(
    session: Session,
    meter_id: int,
    phase: PhaseSel,
    granularity: Granularity,
    time_range: TimeRange,
) -> dict[str, float]:
    bucket = _bucket_label(EMMetric.recorded_at, granularity)
    if phase is PhaseSel.total:
        delta_wh = func.max(EMMetric.total_act_energy) - func.min(
            EMMetric.total_act_energy
        )
        stmt = _meter_base(
            select(bucket.label("bucket"), delta_wh / _WH_PER_KWH),
            meter_id,
            time_range,
        )
    else:
        delta_wh = func.max(Phase.total_act_energy) - func.min(Phase.total_act_energy)
        stmt = _phase_base(
            select(bucket.label("bucket"), delta_wh / _WH_PER_KWH),
            meter_id,
            phase,
            time_range,
        )
    return _run(session, stmt.group_by("bucket").order_by("bucket"))


def _meter_base(
    stmt: Select, meter_id: int, time_range: TimeRange
) -> Select:
    return stmt.where(
        EMMetric.em_id == meter_id,
        EMMetric.recorded_at >= time_range.start,
        EMMetric.recorded_at < time_range.end,
    )


def _phase_base(
    stmt: Select, meter_id: int, phase: PhaseSel, time_range: TimeRange
) -> Select:
    return stmt.join(Phase, Phase.em_metric_id == EMMetric.id).where(
        EMMetric.em_id == meter_id,
        Phase.name == phase.value,
        EMMetric.recorded_at >= time_range.start,
        EMMetric.recorded_at < time_range.end,
    )


def _bucket_label(column: object, granularity: Granularity):
    return func.strftime(_STRFTIME_FORMAT[granularity], column)


def _run(session: Session, stmt: Select) -> dict[str, float]:
    """Execute a (bucket, value) query into a bucket-keyed mapping."""
    return {
        bucket: float(value)
        for bucket, value in session.execute(stmt)
        if bucket is not None and value is not None
    }


def _densify(
    values: dict[str, float],
    granularity: Granularity,
    time_range: TimeRange,
) -> list[TimeseriesPoint]:
    """Expand sparse query results into every expected bucket in the range.

    Buckets with no data get a ``None`` value so the frontend can distinguish
    a gap from a genuine zero.
    """
    fmt = _STRFTIME_FORMAT[granularity]
    points: list[TimeseriesPoint] = []
    for moment in _iter_buckets(time_range, granularity):
        label = moment.strftime(fmt)
        points.append(TimeseriesPoint(bucket=label, value=values.get(label)))
    return points


def _iter_buckets(
    time_range: TimeRange, granularity: Granularity
) -> list[datetime.datetime]:
    moments: list[datetime.datetime] = []
    current = _truncate(time_range.start, granularity)
    while current < time_range.end:
        moments.append(current)
        current = _advance(current, granularity)
    return moments


def _truncate(
    moment: datetime.datetime, granularity: Granularity
) -> datetime.datetime:
    if granularity is Granularity.minute:
        return moment.replace(second=0, microsecond=0)
    if granularity is Granularity.hour:
        return moment.replace(minute=0, second=0, microsecond=0)
    if granularity is Granularity.day:
        return moment.replace(hour=0, minute=0, second=0, microsecond=0)
    return moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _advance(
    moment: datetime.datetime, granularity: Granularity
) -> datetime.datetime:
    if granularity is Granularity.minute:
        return moment + datetime.timedelta(minutes=1)
    if granularity is Granularity.hour:
        return moment + datetime.timedelta(hours=1)
    if granularity is Granularity.day:
        return moment + datetime.timedelta(days=1)
    year, month = divmod(moment.month, 12)
    return moment.replace(year=moment.year + year, month=month + 1)


def _estimate_bucket_count(
    start: datetime.datetime, end: datetime.datetime, granularity: Granularity
) -> int:
    span = end - start
    if granularity is Granularity.minute:
        return int(span.total_seconds() // 60)
    if granularity is Granularity.hour:
        return int(span.total_seconds() // 3600)
    if granularity is Granularity.day:
        return span.days
    return (end.year - start.year) * 12 + (end.month - start.month) + 1
