"""Smart-plug endpoints: device list, latest reading, boosts, and time series."""

import datetime
import logging
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from falk.iot.tuya import Switch
from falk.models.devices import SmartSwitch, SwitchMetric, TuyaSwitch
from falk.models.planning import DeviceOverride
from falk.overrides import clear_boost_for_switch, set_boost_for_switch, utc_now

from ..aggregation import (
    plug_cost_series,
    plug_heatmap,
    plug_statistics,
    plug_timeseries,
)
from ..deps import DeviceSeriesQueryDep, PlugSeriesQueryDep, SessionDep
from ..schemas import (
    BoostClearOut,
    BoostIn,
    BoostOut,
    CostPoint,
    CostSeriesOut,
    HeatmapCell,
    HeatmapOut,
    PlugLatestOut,
    PlugOut,
    PlugStateIn,
    PlugStateOut,
    PlugStatsOut,
    TimeseriesOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugs", tags=["plugs"])


def _actuate(plug: TuyaSwitch, on: bool) -> None:
    """Drive a Tuya plug on/off over the LAN (blocking call).

    Raises:
        Exception: Propagates any tinytuya/LAN error so callers can decide how
            to surface it.
    """
    assert plug.ip is not None, "callers must reject plugs without an IP"
    switch = Switch(
        id=plug.tuya_id,
        name=plug.name,
        ip=plug.ip,
        local_key=plug.local_key,
        version=plug.version,
    )
    if on:
        switch.turn_on()
    else:
        switch.turn_off()


@router.get("")
def list_plugs(session: SessionDep) -> list[PlugOut]:
    """List all smart plugs."""
    plugs = session.scalars(select(SmartSwitch)).all()
    return [PlugOut.model_validate(plug) for plug in plugs]


def _boost_out(override: DeviceOverride, now: datetime.datetime) -> BoostOut:
    """Build a BoostOut, computing the remaining seconds from ``now``."""
    remaining = int((override.until_utc - now).total_seconds())
    return BoostOut(
        plug_id=override.switch_id,
        desired_state=override.desired_state,
        until=override.until_utc,
        remaining_seconds=max(remaining, 0),
    )


@router.get("/boosts")
def list_boosts(session: SessionDep) -> list[BoostOut]:
    """List every currently active boost (one query for the whole dashboard)."""
    now = utc_now()
    overrides = session.scalars(
        select(DeviceOverride).where(DeviceOverride.until_utc > now)
    ).all()
    return [_boost_out(override, now) for override in overrides]


@router.post("/{plug_id}/boost")
def start_boost(plug_id: int, body: BoostIn, session: SessionDep) -> BoostOut:
    """Force a plug on/off for a duration, overriding the price plan.

    The override is persisted first, then the plug is actuated immediately as a
    best effort; if the LAN call fails the override still stands so the periodic
    ``apply`` job retries and reverts it on expiry.
    """
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

    now = utc_now()
    until = set_boost_for_switch(
        session,
        plug.id,
        desired_on=body.on,
        duration=datetime.timedelta(minutes=body.duration_minutes),
        now_utc=now,
    )

    try:
        # Blocking LAN call; FastAPI runs this sync handler in a threadpool.
        _actuate(plug, body.on)
        plug.state = body.on
    except Exception:
        logger.warning(
            "Boost saved for plug %s but immediate actuation failed; "
            "apply will retry",
            plug_id,
            exc_info=True,
        )

    session.commit()
    return _boost_out(
        DeviceOverride(switch_id=plug.id, desired_state=body.on, until_utc=until),
        now,
    )


@router.delete("/{plug_id}/boost")
def clear_boost(plug_id: int, session: SessionDep) -> BoostClearOut:
    """Cancel a plug's boost; the next ``apply`` resumes the price plan."""
    plug = session.get(TuyaSwitch, plug_id)
    if plug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"plug {plug_id} not found",
        )
    cleared = clear_boost_for_switch(session, plug.id)
    session.commit()
    return BoostClearOut(plug_id=plug_id, cleared=cleared)


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

    try:
        # Blocking LAN call; FastAPI runs this sync handler in a threadpool.
        _actuate(plug, body.on)
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


@router.get("/{plug_id}/cost-series")
def plug_cost(
    plug_id: int, query: DeviceSeriesQueryDep, session: SessionDep
) -> CostSeriesOut:
    """Return the plug's estimated energy crossed with hourly PVPC prices."""
    series = plug_cost_series(
        session,
        plug_id,
        granularity=query.granularity,
        time_range=query.time_range,
    )
    return CostSeriesOut(
        plug_id=plug_id,
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
