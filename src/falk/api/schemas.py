"""Pydantic response and query models for the Falk web API.

These models define the JSON contract consumed by the React frontend. All
datetimes are naive-local (matching how telemetry stores ``recorded_at``).
"""

import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Metric(StrEnum):
    """Quantity plotted in a time series."""

    power = "power"  # average active power, in watts
    energy = "energy"  # consumed energy, in kilowatt-hours


class Granularity(StrEnum):
    """Time bucket size for a series."""

    minute = "minute"
    hour = "hour"
    day = "day"
    month = "month"


class PhaseSel(StrEnum):
    """Phase selector for energy-meter series."""

    total = "total"
    l1 = "l1"
    l2 = "l2"
    l3 = "l3"


class MeterOut(BaseModel):
    """An energy meter device."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    model: str
    location: str | None = None
    enabled: bool


class PhaseReading(BaseModel):
    """Instantaneous reading for a single phase."""

    name: str
    act_power: float
    current: float
    voltage: float
    pf: float


class MeterLatestOut(BaseModel):
    """Most recent meter reading, used to drive the dashboard gauges."""

    meter_id: int
    recorded_at: datetime.datetime
    total_act_power: float
    total_current: float
    total_act_energy: float
    phases: list[PhaseReading]


class RankedDevice(BaseModel):
    """A device's consumption value in the ranking."""

    id: int
    name: str
    value: float


class RankingOut(BaseModel):
    """Devices ranked by power (W) or energy (kWh), plus the unassigned rest."""

    meter_id: int
    metric: Metric
    unit: str
    window_days: int
    total: float
    unassigned: float
    devices: list[RankedDevice]


class BreakdownDevice(BaseModel):
    """A device's share of the latest household consumption."""

    id: int
    name: str
    power: float


class BreakdownOut(BaseModel):
    """Latest total consumption split across devices plus the unassigned rest."""

    meter_id: int
    recorded_at: datetime.datetime
    total_act_power: float
    assigned: float
    unassigned: float
    devices: list[BreakdownDevice]


class PlugOut(BaseModel):
    """A smart plug device."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    model: str
    location: str | None = None
    state: bool
    enabled: bool


class PlugLatestOut(BaseModel):
    """Most recent smart-plug reading."""

    plug_id: int
    recorded_at: datetime.datetime
    power: float
    current: int
    voltage: float


class PlugStatsOut(BaseModel):
    """Descriptive statistics and consumption forecast for a plug."""

    plug_id: int
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
    cost_total_eur: float
    cost_today_eur: float
    cost_last7_eur: float
    forecast_next_day_kwh: float
    forecast_next_30d_kwh: float
    trend_pct: float | None = None


class HeatmapCell(BaseModel):
    """Average power for one (day, hour) cell."""

    day: str
    hour: int
    value: float


class HeatmapOut(BaseModel):
    """Day × hour consumption grid for a plug."""

    plug_id: int
    unit: str
    days: list[str]
    cells: list[HeatmapCell]


class PlugStateIn(BaseModel):
    """Requested on/off state for a plug."""

    on: bool


class PlugStateOut(BaseModel):
    """A plug's state after a switch command."""

    plug_id: int
    state: bool


class BoostIn(BaseModel):
    """Requested manual boost: force a plug on/off for a duration."""

    on: bool
    duration_minutes: int = Field(ge=1, le=1440)


class BoostOut(BaseModel):
    """An active boost on a plug."""

    plug_id: int
    desired_state: bool
    until: datetime.datetime
    remaining_seconds: int


class BoostClearOut(BaseModel):
    """Result of clearing a plug's boost."""

    plug_id: int
    cleared: bool


class MeterStatsOut(BaseModel):
    """Descriptive power statistics and an energy trend/forecast for a meter."""

    meter_id: int
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
    trend_pct: float | None = None


class DeviceSeriesEntry(BaseModel):
    """One device's energy values aligned to the shared ``buckets`` axis."""

    id: int
    name: str
    values: list[float]


class DeviceSeriesOut(BaseModel):
    """Per-device energy series for a stacked area chart, plus the unassigned rest."""

    meter_id: int
    granularity: Granularity
    unit: str
    buckets: list[str]
    devices: list[DeviceSeriesEntry]
    unassigned: list[float]


class CostPoint(BaseModel):
    """One bucket's energy (kWh), effective price (€/kWh) and cost (€).

    Any field is null for buckets without metered energy or without a price.
    """

    bucket: str
    energy_kwh: float | None
    price_kwh: float | None
    cost_eur: float | None


class CostSeriesOut(BaseModel):
    """Energy crossed with PVPC prices, bucketed, plus window totals.

    Carries either a ``meter_id`` (meter-level cost) or a ``plug_id``
    (per-device cost); the other is null.
    """

    meter_id: int | None = None
    plug_id: int | None = None
    granularity: Granularity
    points: list[CostPoint]
    total_energy_kwh: float
    total_cost_eur: float
    avg_price_kwh: float


class TimeseriesPoint(BaseModel):
    """A single bucketed value. ``value`` is null for buckets without data."""

    bucket: str
    value: float | None


class TimeseriesOut(BaseModel):
    """A bucketed time series for a meter or a plug."""

    metric: Metric
    granularity: Granularity
    unit: str
    phase: PhaseSel | None = None
    meter_id: int | None = None
    plug_id: int | None = None
    points: list[TimeseriesPoint]
