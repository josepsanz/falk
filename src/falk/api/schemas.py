"""Pydantic response and query models for the Falk web API.

These models define the JSON contract consumed by the React frontend. All
datetimes are naive-local (matching how telemetry stores ``recorded_at``).
"""

import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


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
