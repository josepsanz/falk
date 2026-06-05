"""Smart-plug endpoints: device list, latest reading, and time series."""

import datetime
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from falk.iot.tuya import Switch
from falk.models.devices import SmartSwitch, SwitchMetric, TuyaSwitch

from ..aggregation import plug_heatmap, plug_statistics, plug_timeseries
from ..deps import PlugSeriesQueryDep, SessionDep
from ..schemas import (
    HeatmapCell,
    HeatmapOut,
    PlugLatestOut,
    PlugOut,
    PlugStateIn,
    PlugStateOut,
    PlugStatsOut,
    TimeseriesOut,
)

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


@router.get("/{plug_id}/stats")
def plug_stats(
    plug_id: int,
    session: SessionDep,
    window_days: Annotated[int, Query(ge=1, le=90)] = 30,
) -> PlugStatsOut:
    """Descriptive statistics and a consumption forecast for a plug."""
    stats = plug_statistics(
        session, plug_id, window_days=window_days, now=datetime.datetime.now()
    )
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no readings for plug {plug_id}",
        )
    return PlugStatsOut(plug_id=plug_id, **asdict(stats))


@router.get("/{plug_id}/heatmap")
def plug_heatmap_grid(
    plug_id: int,
    session: SessionDep,
    days: Annotated[int, Query(ge=1, le=60)] = 14,
) -> HeatmapOut:
    """Day × hour grid of average plug power over the last ``days`` days."""
    rows = plug_heatmap(
        session, plug_id, days=days, now=datetime.datetime.now()
    )
    day_list = sorted({day for day, _, _ in rows})
    cells = [HeatmapCell(day=day, hour=hour, value=value) for day, hour, value in rows]
    return HeatmapOut(plug_id=plug_id, unit="W", days=day_list, cells=cells)


@router.post("/{plug_id}/state")
def set_plug_state(
    plug_id: int, body: PlugStateIn, session: SessionDep
) -> PlugStateOut:
    """Turn a Tuya plug on or off over the LAN and persist its state."""
    plug = session.get(TuyaSwitch, plug_id)
    if plug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"plug {plug_id} not found",
        )
    if plug.ip is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"plug {plug_id} has no IP configured",
        )

    switch = Switch(
        id=plug.tuya_id,
        name=plug.name,
        ip=plug.ip,
        local_key=plug.local_key,
        version=plug.version,
    )
    try:
        # Blocking LAN call; FastAPI runs this sync handler in a threadpool.
        if body.on:
            switch.turn_on()
        else:
            switch.turn_off()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="could not reach the device",
        ) from exc

    plug.state = body.on
    session.commit()
    return PlugStateOut(plug_id=plug_id, state=body.on)


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
