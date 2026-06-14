"""Outbound alerting channels for the telemetry and control jobs."""

from .telegram import send_alert

__all__ = ["send_alert"]
