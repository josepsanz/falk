"""Smart-plug endpoints: device list, latest reading, and time series."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from falk.models.devices import SmartSwitch, SwitchMetric

from ..aggregation import plug_timeseries
from ..deps import PlugSeriesQueryDep, SessionDep
from ..schemas import PlugLatestOut, PlugOut, TimeseriesOut

router = APIRouter(prefix="/plugs", tags=["plugs"])


@router.get("")
def list_plugs(session: SessionDep) -> list[PlugOut]:
    """List all smart plugs."""
    plugs = session.scalars(select(SmartSwitch)).all()
    return [PlugOut.model_validate(plug) for plug in plugs]


@router.get("/{plug_id}/latest")
def latest_plug_reading(plug_id: int, session: SessionDep) -> PlugLatestOut:
    """Return the most recent reading for a plug."""
    metric = session.scalars(
        select(SwitchMetric)
        .where(SwitchMetric.switch_id == plug_id)
        .order_by(SwitchMetric.recorded_at.desc())
        .limit(1)
    ).first()
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for plug {plug_id}",
        )
    return PlugLatestOut(
        plug_id=plug_id,
        recorded_at=metric.recorded_at,
        power=metric.power,
        current=metric.current,
        voltage=metric.voltage,
    )


@router.get("/{plug_id}/timeseries")
def plug_series(
    plug_id: int, query: PlugSeriesQueryDep, session: SessionDep
) -> TimeseriesOut:
    """Return a bucketed power or (approximate) energy series for a plug."""
    unit, points = plug_timeseries(
        session,
        plug_id,
        metric=query.metric,
        granularity=query.granularity,
        time_range=query.time_range,
    )
    return TimeseriesOut(
        metric=query.metric,
        granularity=query.granularity,
        unit=unit,
        plug_id=plug_id,
        points=points,
    )
