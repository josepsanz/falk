"""Time-series aggregation queries over the SQLite metrics tables.

All bucketing is done with SQLite ``strftime`` on the naive-local ``recorded_at``
column. Power series average the instantaneous samples; energy series derive
consumption from the cumulative Wh counters (meters) or by integrating power
over the sampling interval (plugs, which lack a cumulative counter).
"""

import datetime
import statistics
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import Integer, Select, func, select
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


@dataclass(frozen=True, slots=True)
class RankedDevice:
    """A device's consumption value (W or kWh) for the ranking."""

    id: int
    name: str
    value: float


@dataclass(frozen=True, slots=True)
class Ranking:
    """Devices ranked by consumption, plus the unassigned remainder."""

    total: float
    unassigned: float
    devices: list[RankedDevice]


def device_ranking(
    session: Session,
    meter_id: int,
    *,
    metric: Metric,
    window_days: int,
    now: datetime.datetime,
) -> Ranking | None:
    """Rank devices by current power (W) or energy consumed over a window (kWh)."""
    if metric is Metric.power:
        breakdown = consumption_breakdown(session, meter_id)
        if breakdown is None:
            return None
        devices = [
            RankedDevice(id=d.id, name=d.name, value=d.power)
            for d in breakdown.devices
        ]
        return Ranking(
            total=breakdown.total_act_power,
            unassigned=breakdown.unassigned,
            devices=devices,
        )

    start = now - datetime.timedelta(days=window_days)
    meter_wh = session.scalar(
        select(
            func.max(EMMetric.total_act_energy) - func.min(EMMetric.total_act_energy)
        ).where(EMMetric.em_id == meter_id, EMMetric.recorded_at >= start)
    )
    meter_kwh = (meter_wh or 0.0) / _WH_PER_KWH

    rows = session.execute(
        select(SmartSwitch.id, SmartSwitch.name, func.sum(SwitchMetric.power))
        .join(SwitchMetric, SwitchMetric.switch_id == SmartSwitch.id)
        .where(
            SmartSwitch.enabled.is_(True),
            SwitchMetric.recorded_at >= start,
        )
        .group_by(SmartSwitch.id, SmartSwitch.name)
    ).all()
    devices = [
        RankedDevice(
            id=switch_id,
            name=name,
            value=round(
                float(power_sum) * _PLUG_SAMPLE_INTERVAL_HOURS / _WH_PER_KWH, 3
            ),
        )
        for switch_id, name, power_sum in rows
        if power_sum is not None
    ]
    devices.sort(key=lambda device: device.value, reverse=True)
    assigned = sum(device.value for device in devices)
    unassigned = max(0.0, meter_kwh - assigned)
    total = meter_kwh if meter_kwh > 0 else assigned
    return Ranking(total=total, unassigned=round(unassigned, 3), devices=devices)


@dataclass(frozen=True, slots=True)
class DeviceEnergyEntry:
    """One device's bucketed energy consumption (kWh per bucket)."""

    id: int
    name: str
    values: list[float]


@dataclass(frozen=True, slots=True)
class DeviceEnergySeries:
    """Per-device energy series sharing a common bucket axis, plus the rest.

    ``unassigned`` is the household energy not metered by any plug (the meter's
    consumption minus the sum of plug draws per bucket, clamped at zero), so the
    device series and the unassigned series stack up to the household total.
    """

    buckets: list[str]
    devices: list[DeviceEnergyEntry]
    unassigned: list[float]


def device_energy_series(
    session: Session,
    meter_id: int,
    *,
    granularity: Granularity,
    time_range: TimeRange,
) -> DeviceEnergySeries:
    """Build a per-device energy (kWh) series for stacking over a time range.

    Each enabled plug becomes a series of energy-per-bucket values (power
    integrated over the sampling interval), densified to every bucket in the
    range with ``0.0`` where the plug recorded nothing. The unassigned series
    is the meter's per-bucket energy minus the summed plug energy.
    """
    bucket = _bucket_label(SwitchMetric.recorded_at, granularity)
    energy_expr = func.sum(SwitchMetric.power) * (
        _PLUG_SAMPLE_INTERVAL_HOURS / _WH_PER_KWH
    )
    rows = session.execute(
        select(
            SmartSwitch.id,
            SmartSwitch.name,
            bucket.label("bucket"),
            energy_expr.label("value"),
        )
        .join(SwitchMetric, SwitchMetric.switch_id == SmartSwitch.id)
        .where(
            SmartSwitch.enabled.is_(True),
            SwitchMetric.recorded_at >= time_range.start,
            SwitchMetric.recorded_at < time_range.end,
        )
        .group_by(SmartSwitch.id, "bucket")
        .order_by(SmartSwitch.id, "bucket")
    ).all()

    labels = [
        moment.strftime(_STRFTIME_FORMAT[granularity])
        for moment in _iter_buckets(time_range, granularity)
    ]

    names: dict[int, str] = {}
    by_device: dict[int, dict[str, float]] = defaultdict(dict)
    for switch_id, name, bucket_label, value in rows:
        if bucket_label is None or value is None:
            continue
        names[switch_id] = name
        by_device[switch_id][bucket_label] = round(float(value), 3)

    devices = [
        DeviceEnergyEntry(
            id=switch_id,
            name=names[switch_id],
            values=[buckets.get(label, 0.0) for label in labels],
        )
        for switch_id, buckets in by_device.items()
    ]
    devices.sort(key=lambda d: sum(d.values), reverse=True)

    meter_kwh = _meter_energy_rows(
        session, meter_id, PhaseSel.total, granularity, time_range
    )
    assigned_per_bucket = [
        sum(device.values[i] for device in devices) for i in range(len(labels))
    ]
    unassigned = [
        round(max(0.0, meter_kwh.get(label, 0.0) - assigned_per_bucket[i]), 3)
        for i, label in enumerate(labels)
    ]
    return DeviceEnergySeries(buckets=labels, devices=devices, unassigned=unassigned)


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


_ACTIVE_THRESHOLD_W = 1.0


@dataclass(frozen=True, slots=True)
class MeterStatistics:
    """Descriptive power stats and an energy trend/forecast for an energy meter."""

    window_days: int
    samples: int
    power_now: float
    power_avg: float
    power_min: float
    power_max: float
    power_median: float
    power_p95: float
    energy_total_kwh: float
    energy_daily_avg_kwh: float
    energy_today_kwh: float
    energy_last7_kwh: float
    forecast_next_day_kwh: float
    forecast_next_30d_kwh: float
    trend_pct: float | None


def meter_statistics(
    session: Session,
    meter_id: int,
    *,
    window_days: int,
    now: datetime.datetime,
) -> MeterStatistics | None:
    """Compute power statistics and an energy trend/forecast for a meter.

    Power stats summarise the instantaneous ``total_act_power`` samples. Energy
    is derived per day from the cumulative Wh counter (MAX−MIN), which is more
    accurate than integrating power; the forecast is the recent 7-day average
    daily energy, with a trend comparing the last 7 days to the previous 7.
    """
    start = now - datetime.timedelta(days=window_days)
    rows = session.execute(
        select(
            EMMetric.recorded_at,
            EMMetric.total_act_power,
            EMMetric.total_act_energy,
        )
        .where(EMMetric.em_id == meter_id, EMMetric.recorded_at >= start)
        .order_by(EMMetric.recorded_at)
    ).all()
    if not rows:
        return None

    powers = [float(power) for _, power, _ in rows]
    sample_count = len(powers)
    p95 = (
        statistics.quantiles(powers, n=20)[18]
        if sample_count >= 2
        else powers[0]
    )

    # Daily energy from the cumulative counter: last reading minus first per day.
    counters_by_day: dict[datetime.date, list[float]] = defaultdict(list)
    for recorded_at, _, energy in rows:
        counters_by_day[recorded_at.date()].append(float(energy))
    energy_per_day = {
        day: (max(values) - min(values)) / _WH_PER_KWH
        for day, values in counters_by_day.items()
    }

    today = now.date()
    daily_values = list(energy_per_day.values())
    total_kwh = sum(daily_values)
    daily_avg = total_kwh / len(daily_values)

    recent7 = [
        kwh
        for day, kwh in energy_per_day.items()
        if day > today - datetime.timedelta(days=7)
    ]
    prev7 = [
        kwh
        for day, kwh in energy_per_day.items()
        if today - datetime.timedelta(days=14)
        < day
        <= today - datetime.timedelta(days=7)
    ]
    recent7_avg = statistics.mean(recent7) if recent7 else daily_avg

    trend_pct: float | None = None
    if recent7 and prev7:
        prev7_avg = statistics.mean(prev7)
        if prev7_avg > 0:
            trend_pct = (recent7_avg - prev7_avg) / prev7_avg * 100

    return MeterStatistics(
        window_days=window_days,
        samples=sample_count,
        power_now=round(powers[-1], 1),
        power_avg=round(statistics.mean(powers), 1),
        power_min=round(min(powers), 1),
        power_max=round(max(powers), 1),
        power_median=round(statistics.median(powers), 1),
        power_p95=round(p95, 1),
        energy_total_kwh=round(total_kwh, 3),
        energy_daily_avg_kwh=round(daily_avg, 3),
        energy_today_kwh=round(energy_per_day.get(today, 0.0), 3),
        energy_last7_kwh=round(sum(recent7), 3),
        forecast_next_day_kwh=round(recent7_avg, 3),
        forecast_next_30d_kwh=round(recent7_avg * 30, 3),
        trend_pct=round(trend_pct, 1) if trend_pct is not None else None,
    )


@dataclass(frozen=True, slots=True)
class PlugStatistics:
    """Descriptive statistics and a simple consumption forecast for a plug."""

    window_days: int
    samples: int
    power_avg: float
    power_min: float
    power_max: float
    power_median: float
    power_p95: float
    active_ratio: float
    energy_total_kwh: float
    energy_daily_avg_kwh: float
    energy_today_kwh: float
    energy_last7_kwh: float
    forecast_next_day_kwh: float
    forecast_next_30d_kwh: float
    trend_pct: float | None


def plug_statistics(
    session: Session,
    plug_id: int,
    *,
    window_days: int,
    now: datetime.datetime,
) -> PlugStatistics | None:
    """Compute descriptive power stats and an energy forecast over a window.

    Energy is approximated as power × sampling interval (plugs have no
    cumulative counter); the forecast is the recent 7-day average daily energy,
    with a trend from comparing the last 7 days to the previous 7.
    """
    start = now - datetime.timedelta(days=window_days)
    rows = session.execute(
        select(SwitchMetric.recorded_at, SwitchMetric.power)
        .where(
            SwitchMetric.switch_id == plug_id,
            SwitchMetric.recorded_at >= start,
        )
        .order_by(SwitchMetric.recorded_at)
    ).all()
    if not rows:
        return None

    powers = [float(power) for _, power in rows]
    sample_count = len(powers)
    p95 = (
        statistics.quantiles(powers, n=20)[18]
        if sample_count >= 2
        else powers[0]
    )
    active_ratio = sum(p > _ACTIVE_THRESHOLD_W for p in powers) / sample_count

    energy_per_day: dict[datetime.date, float] = defaultdict(float)
    for recorded_at, power in rows:
        energy_per_day[recorded_at.date()] += (
            float(power) * _PLUG_SAMPLE_INTERVAL_HOURS / _WH_PER_KWH
        )

    today = now.date()
    daily_values = list(energy_per_day.values())
    total_kwh = sum(daily_values)
    daily_avg = total_kwh / len(daily_values)

    recent7 = [
        kwh
        for day, kwh in energy_per_day.items()
        if day > today - datetime.timedelta(days=7)
    ]
    prev7 = [
        kwh
        for day, kwh in energy_per_day.items()
        if today - datetime.timedelta(days=14) < day <= today - datetime.timedelta(days=7)
    ]
    recent7_avg = statistics.mean(recent7) if recent7 else daily_avg

    trend_pct: float | None = None
    if recent7 and prev7:
        prev7_avg = statistics.mean(prev7)
        if prev7_avg > 0:
            trend_pct = (recent7_avg - prev7_avg) / prev7_avg * 100

    return PlugStatistics(
        window_days=window_days,
        samples=sample_count,
        power_avg=round(statistics.mean(powers), 1),
        power_min=round(min(powers), 1),
        power_max=round(max(powers), 1),
        power_median=round(statistics.median(powers), 1),
        power_p95=round(p95, 1),
        active_ratio=round(active_ratio, 3),
        energy_total_kwh=round(total_kwh, 3),
        energy_daily_avg_kwh=round(daily_avg, 3),
        energy_today_kwh=round(energy_per_day.get(today, 0.0), 3),
        energy_last7_kwh=round(sum(recent7), 3),
        forecast_next_day_kwh=round(recent7_avg, 3),
        forecast_next_30d_kwh=round(recent7_avg * 30, 3),
        trend_pct=round(trend_pct, 1) if trend_pct is not None else None,
    )


def plug_heatmap(
    session: Session,
    plug_id: int,
    *,
    days: int,
    now: datetime.datetime,
) -> list[tuple[str, int, float]]:
    """Average plug power per (day, hour) cell over the last ``days`` days.

    Returns (day 'YYYY-MM-DD', hour 0–23, average watts) tuples.
    """
    start = now - datetime.timedelta(days=days)
    day_label = func.strftime("%Y-%m-%d", SwitchMetric.recorded_at).label("day")
    hour_label = func.cast(
        func.strftime("%H", SwitchMetric.recorded_at), Integer
    ).label("hour")
    stmt = (
        select(day_label, hour_label, func.avg(SwitchMetric.power).label("value"))
        .where(
            SwitchMetric.switch_id == plug_id,
            SwitchMetric.recorded_at >= start,
        )
        .group_by(day_label, hour_label)
        .order_by(day_label, hour_label)
    )
    return [
        (day, int(hour), round(float(value), 1))
        for day, hour, value in session.execute(stmt)
        if day is not None and hour is not None and value is not None
    ]


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
