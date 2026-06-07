"""FastAPI dependencies shared across routers."""

import datetime
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from falk.db import session_factory

from .aggregation import BucketRangeTooLargeError, TimeRange, resolve_range
from .schemas import Granularity, Metric, PhaseSel


def get_session() -> Iterator[Session]:
    """Yield a database session scoped to a single request."""
    with session_factory()() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@dataclass(frozen=True, slots=True)
class SeriesQuery:
    """Validated query parameters for a time-series request."""

    metric: Metric
    granularity: Granularity
    phase: PhaseSel
    time_range: TimeRange


def _resolve(
    granularity: Granularity,
    dt_from: datetime.datetime | None,
    dt_to: datetime.datetime | None,
) -> TimeRange:
    try:
        return resolve_range(
            granularity, dt_from, dt_to, now=datetime.datetime.now()
        )
    except BucketRangeTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


def meter_series_query(
    metric: Annotated[Metric, Query()] = Metric.power,
    granularity: Annotated[Granularity, Query()] = Granularity.hour,
    phase: Annotated[PhaseSel, Query()] = PhaseSel.total,
    dt_from: Annotated[datetime.datetime | None, Query(alias="from")] = None,
    dt_to: Annotated[datetime.datetime | None, Query(alias="to")] = None,
) -> SeriesQuery:
    """Parse and validate the query parameters for a meter series."""
    return SeriesQuery(
        metric=metric,
        granularity=granularity,
        phase=phase,
        time_range=_resolve(granularity, dt_from, dt_to),
    )


@dataclass(frozen=True, slots=True)
class DeviceSeriesQuery:
    """Validated query parameters for a per-device energy series request."""

    granularity: Granularity
    time_range: TimeRange


def device_series_query(
    granularity: Annotated[Granularity, Query()] = Granularity.day,
    dt_from: Annotated[datetime.datetime | None, Query(alias="from")] = None,
    dt_to: Annotated[datetime.datetime | None, Query(alias="to")] = None,
) -> DeviceSeriesQuery:
    """Parse and validate the query parameters for a per-device energy series."""
    return DeviceSeriesQuery(
        granularity=granularity,
        time_range=_resolve(granularity, dt_from, dt_to),
    )


def plug_series_query(
    metric: Annotated[Metric, Query()] = Metric.power,
    granularity: Annotated[Granularity, Query()] = Granularity.hour,
    dt_from: Annotated[datetime.datetime | None, Query(alias="from")] = None,
    dt_to: Annotated[datetime.datetime | None, Query(alias="to")] = None,
) -> SeriesQuery:
    """Parse and validate the query parameters for a plug series."""
    return SeriesQuery(
        metric=metric,
        granularity=granularity,
        phase=PhaseSel.total,
        time_range=_resolve(granularity, dt_from, dt_to),
    )


MeterSeriesQueryDep = Annotated[SeriesQuery, Depends(meter_series_query)]
PlugSeriesQueryDep = Annotated[SeriesQuery, Depends(plug_series_query)]
DeviceSeriesQueryDep = Annotated[DeviceSeriesQuery, Depends(device_series_query)]
