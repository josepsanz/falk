"""Energy-meter endpoints: device list, latest reading, and time series."""

import dataclasses
import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from falk.models.devices import EMMetric, EnergyMeter

from ..aggregation import (
    consumption_breakdown,
    device_energy_series,
    device_ranking,
    meter_cost_series,
    meter_statistics,
    meter_timeseries,
)
from ..deps import DeviceSeriesQueryDep, MeterSeriesQueryDep, SessionDep
from ..schemas import (
    BreakdownDevice,
    BreakdownOut,
    CostPoint,
    CostSeriesOut,
    DeviceSeriesEntry,
    DeviceSeriesOut,
    MeterLatestOut,
    MeterOut,
    MeterStatsOut,
    Metric,
    PhaseReading,
    RankedDevice,
    RankingOut,
    TimeseriesOut,
)

router = APIRouter(prefix="/meters", tags=["meters"])


@router.get("")
def list_meters(session: SessionDep) -> list[MeterOut]:
    """List all energy meters."""
    meters = session.scalars(select(EnergyMeter)).all()
    return [MeterOut.model_validate(meter) for meter in meters]


@router.get("/{meter_id}/latest")
def latest_meter_reading(meter_id: int, session: SessionDep) -> MeterLatestOut:
    """Return the most recent reading for a meter, for the dashboard gauges."""
    metric = session.scalars(
        select(EMMetric)
        .where(EMMetric.em_id == meter_id)
        .order_by(EMMetric.recorded_at.desc())
        .limit(1)
    ).first()
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for meter {meter_id}",
        )
    return MeterLatestOut(
        meter_id=meter_id,
        recorded_at=metric.recorded_at,
        total_act_power=metric.total_act_power,
        total_current=metric.total_current,
        total_act_energy=metric.total_act_energy,
        phases=[
            PhaseReading(
                name=phase.name,
                act_power=phase.act_power,
                current=phase.current,
                voltage=phase.voltage,
                pf=phase.pf,
            )
            for phase in sorted(metric.phases, key=lambda p: p.name)
        ],
    )


@router.get("/{meter_id}/breakdown")
def meter_breakdown(meter_id: int, session: SessionDep) -> BreakdownOut:
    """Split the meter's latest total power across plugs plus the unassigned rest."""
    breakdown = consumption_breakdown(session, meter_id)
    if breakdown is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for meter {meter_id}",
        )
    return BreakdownOut(
        meter_id=meter_id,
        recorded_at=breakdown.recorded_at,
        total_act_power=breakdown.total_act_power,
        assigned=breakdown.assigned,
        unassigned=breakdown.unassigned,
        devices=[
            BreakdownDevice(id=device.id, name=device.name, power=device.power)
            for device in breakdown.devices
        ],
    )


@router.get("/{meter_id}/ranking")
def meter_ranking(
    meter_id: int,
    session: SessionDep,
    metric: Annotated[Metric, Query()] = Metric.power,
    window_days: Annotated[int, Query(ge=1, le=90)] = 7,
) -> RankingOut:
    """Rank devices by current power (W) or energy over a window (kWh)."""
    ranking = device_ranking(
        session,
        meter_id,
        metric=metric,
        window_days=window_days,
        now=datetime.datetime.now(),
    )
    if ranking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for meter {meter_id}",
        )
    return RankingOut(
        meter_id=meter_id,
        metric=metric,
        unit="W" if metric is Metric.power else "kWh",
        window_days=window_days,
        total=ranking.total,
        unassigned=ranking.unassigned,
        devices=[
            RankedDevice(id=d.id, name=d.name, value=d.value)
            for d in ranking.devices
        ],
    )


@router.get("/{meter_id}/stats")
def meter_stats(
    meter_id: int,
    session: SessionDep,
    window_days: Annotated[int, Query(ge=1, le=90)] = 30,
) -> MeterStatsOut:
    """Descriptive power statistics and an energy trend/forecast for a meter."""
    stats = meter_statistics(
        session,
        meter_id,
        window_days=window_days,
        now=datetime.datetime.now(),
    )
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for meter {meter_id}",
        )
    return MeterStatsOut(meter_id=meter_id, **dataclasses.asdict(stats))


@router.get("/{meter_id}/device-series")
def meter_device_series(
    meter_id: int, query: DeviceSeriesQueryDep, session: SessionDep
) -> DeviceSeriesOut:
    """Return a per-device energy series (kWh per bucket) for a stacked area chart."""
    series = device_energy_series(
        session,
        meter_id,
        granularity=query.granularity,
        time_range=query.time_range,
    )
    return DeviceSeriesOut(
        meter_id=meter_id,
        granularity=query.granularity,
        unit="kWh",
        buckets=series.buckets,
        devices=[
            DeviceSeriesEntry(id=d.id, name=d.name, values=d.values)
            for d in series.devices
        ],
        unassigned=series.unassigned,
    )


@router.get("/{meter_id}/cost-series")
def meter_cost(
    meter_id: int, query: DeviceSeriesQueryDep, session: SessionDep
) -> CostSeriesOut:
    """Return the meter's energy crossed with hourly PVPC prices (cost in €)."""
    series = meter_cost_series(
        session,
        meter_id,
        granularity=query.granularity,
        time_range=query.time_range,
    )
    return CostSeriesOut(
        meter_id=meter_id,
        granularity=query.granularity,
        points=[
            CostPoint(
                bucket=point.bucket,
                energy_kwh=point.energy_kwh,
                price_kwh=point.price_kwh,
                cost_eur=point.cost_eur,
            )
            for point in series.points
        ],
        total_energy_kwh=series.total_energy_kwh,
        total_cost_eur=series.total_cost_eur,
        avg_price_kwh=series.avg_price_kwh,
    )


@router.get("/{meter_id}/timeseries")
def meter_series(
    meter_id: int, query: MeterSeriesQueryDep, session: SessionDep
) -> TimeseriesOut:
    """Return a bucketed power or energy series for a meter (total or phase)."""
    unit, points = meter_timeseries(
        session,
        meter_id,
        metric=query.metric,
        granularity=query.granularity,
        phase=query.phase,
        time_range=query.time_range,
    )
    return TimeseriesOut(
        metric=query.metric,
        granularity=query.granularity,
        phase=query.phase,
        unit=unit,
        meter_id=meter_id,
        points=points,
    )
