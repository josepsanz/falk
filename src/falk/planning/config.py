"""Schedule configuration parsed from the per-device ``schedule`` block."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Strategy = Literal["cheapest_hours"]


class ScheduleConfig(BaseModel):
    """Price-driven control policy for one device, read from ``devices.yaml``.

    A device is considered *controlled* only when ``enabled`` is true; otherwise
    the ``apply`` job never touches it.
    """

    enabled: bool = False
    strategy: Strategy = "cheapest_hours"
    hours: int = Field(default=0, ge=0, le=24)
    min_guaranteed: list[int] = Field(
        default_factory=list,
        description="Local hours-of-day (0-23) forced ON regardless of price.",
    )
