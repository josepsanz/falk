"""Energy-meter endpoints: device list, latest reading, and time series."""

import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from falk.models.devices import EMMetric, EnergyMeter

from ..aggregation import (
    consumption_breakdown,
    device_ranking,
    meter_timeseries,
)
from ..deps import MeterSeriesQueryDep, SessionDep
from ..schemas import (
    BreakdownDevice,
    BreakdownOut,
    MeterLatestOut,
    MeterOut,
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
