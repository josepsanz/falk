# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run telemetry manually (polls all enabled devices and writes to DB)
uv run python -m falk.telemetry
uv run python -m falk.telemetry --devices-file devices.yaml -v

# Database migrations
alembic upgrade head                                    # apply all pending migrations
alembic revision --autogenerate -m "message"           # generate migration from model diff

# Discover Tuya devices on the network
tinytuya scan
```

There are no tests in this project.

## Architecture

Falk is a home electricity monitoring system. It periodically polls Tuya smart plugs over the local network, records energy metrics, and (optionally) displays them via a web UI.

**Data flow:**
1. `devices.yaml` — source of truth for device configuration (IPs, local keys, Tuya IDs) and the SQLite database URI.
2. `falk/telemetry.py` — the main entry point. Reads `devices.yaml`, connects to each enabled device via `falk.iot.tuya.Switch`, and inserts a `SwitchMetric` row per device per run. Designed to run as a cron job every 5 minutes.
3. `falk/iot/tuya.py` — thin wrapper around `tinytuya.Device`. The `Switch` dataclass communicates with a physical plug over LAN (no cloud). DPS keys: `1`=state, `21`=current (mA), `22`=power (×0.1 W), `23`=voltage (×0.1 V).
4. `falk/models/` — SQLAlchemy ORM models using joined-table inheritance: `SmartSwitch` (base) → `TuyaSwitch` (child). `SwitchMetric` records timestamped readings and has a composite index on `(switch_id, recorded_at)`.

**Database:** SQLite at `falk.db` (path from `devices.yaml`). Alembic manages schema migrations with `render_as_batch=True` (required for SQLite ALTER TABLE support). All models must be imported in `alembic/env.py` for autogenerate to work.

**Adding a new device type:** Subclass `SmartSwitch` with a new `__tablename__` and `polymorphic_identity`, add a corresponding IoT class in `falk/iot/`, and create an Alembic migration.
