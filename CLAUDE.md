# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run telemetry manually. The CLI requires a subcommand:
#   poll    — poll all enabled devices and write metrics to DB (the cron job)
#   pricing — fetch and store ESIOS PVPC hourly prices (--date YYYY-MM-DD, defaults to tomorrow)
#   plan    — compute the per-device on/off plan from stored prices (--date, defaults to tomorrow)
#   apply   — reconcile real device state against the plan/boost (run every ~5 min)
#   boost   — manually force a device ON/OFF for a duration, overriding the plan
uv run python -m falk.telemetry poll
uv run python -m falk.telemetry poll --devices-file devices.yaml -v
uv run python -m falk.telemetry pricing --date 2026-06-12 -v
uv run python -m falk.telemetry plan --date 2026-06-15 -v
uv run python -m falk.telemetry apply -v
uv run python -m falk.telemetry boost TSP003-20A-termo --on --for 2h30m   # force ON for 2h30
uv run python -m falk.telemetry boost TSP003-20A-termo --clear            # cancel the boost

# Cron layout (run from the repo root). pricing → plan → apply; apply every 5 min so
# manual boosts (sub-hour precision) expire on time.
#   */5 * * * *  uv run python -m falk.telemetry poll      # telemetry
#   0   13 * * * uv run python -m falk.telemetry pricing   # fetch tomorrow's prices
#   5   13 * * * uv run python -m falk.telemetry plan      # compute tomorrow's schedule
#   */5 * * * *  uv run python -m falk.telemetry apply      # reconcile state vs plan/boost

# Web dashboard — backend API (FastAPI). Serves the built SPA if present.
uv run uvicorn falk.api.main:app --reload --port 8000   # dev (auto-reload)
uv run falk-api                                          # prod launcher (FALK_API_HOST/PORT)

# Web dashboard — frontend (React + Vite, in frontend/)
cd frontend && npm install && npm run dev   # dev server on :5173, proxies /api -> :8000
cd frontend && npm run build                # builds into src/falk/api/static/ (served by falk-api)

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
2. `falk/telemetry.py` — the main entry point, a subcommand CLI. `poll` reads `devices.yaml`, connects to each enabled device via `falk.iot.tuya.Switch`, and inserts a `SwitchMetric` row per device per run (designed to run as a cron job every 5 minutes). `pricing` fetches and stores ESIOS PVPC hourly prices via `falk.pricing.esios.save_day_prices`.
3. `falk/iot/tuya.py` — thin wrapper around `tinytuya.Device`. The `Switch` dataclass communicates with a physical plug over LAN (no cloud). DPS keys: `1`=state, `21`=current (mA), `22`=power (×0.1 W), `23`=voltage (×0.1 V).
4. `falk/models/` — SQLAlchemy ORM models using joined-table inheritance: `SmartSwitch` (base) → `TuyaSwitch` (child). `SwitchMetric` records timestamped readings and has a composite index on `(switch_id, recorded_at)`.

**Database:** SQLite at `falk.db` (path from `devices.yaml`). Alembic manages schema migrations with `render_as_batch=True` (required for SQLite ALTER TABLE support). All models must be imported in `alembic/env.py` for autogenerate to work.

**Adding a new device type:** Subclass `SmartSwitch` with a new `__tablename__` and `polymorphic_identity`, add a corresponding IoT class in `falk/iot/`, and create an Alembic migration.

**Price-driven scheduling:** Devices with a `schedule` block in `devices.yaml` are controlled by price.
- `falk/planning/config.py` — `ScheduleConfig` (pydantic) parses the per-device `schedule` block (`enabled`, `strategy`, `hours`, `min_guaranteed`). A device is controlled only when `schedule.enabled` is true; without the block it is never actuated.
- `falk/planning/selection.py` — pure strategy functions over the day's prices → set of UTC ON-hours. Only `cheapest_hours` is implemented (dispatched via `match` in `select_on_hours`); `min_guaranteed` local hours are always forced ON.
- `falk/planning/scheduler.py` — `build_plan(day)` reads stored `EsiosPrice` rows for the local day and upserts `DeviceSchedule` rows (one per hour per device). Idempotent.
- `falk/control.py` — `run_apply()` is an idempotent reconciler: it resolves each device's desired state (an active boost wins over the hour's `DeviceSchedule.desired_state`) and only toggles the plug (`Switch.turn_on/off`) when the real state differs. LAN calls are retried with `tenacity`; failures (and missing plans — a safe no-op) are collected and pushed via `falk/alerts/telegram.py`.
- `falk/overrides.py` — manual boost backend, shared by CLI and API. Name-based `set_boost`/`clear_boost` (open their own session, resolve by device name/Tuya id) wrap the session-based core `set_boost_for_switch`/`clear_boost_for_switch` (used by the API with a DB id). Plus `active_override` and `parse_duration` (`2h30m`/`90m`/`1h`). A boost is a `DeviceOverride` row (one per switch) with `until_utc`; it has sub-hour precision, so `apply` should run every ~5 min (not hourly) for the boost to expire on time.
- `falk/models/planning.py` — `DeviceSchedule(switch_id, datetime_utc, desired_state, price_kwh, strategy)` unique on `(switch_id, datetime_utc)`; `DeviceOverride(switch_id, desired_state, until_utc)` unique on `switch_id`.
- Cron order: `pricing` (fetch tomorrow's prices) → `plan` (compute tomorrow's schedule) → `apply` (reconcile every ~5 min). The `telegram` block in `devices.yaml` configures alerts.

**Web dashboard:** A mostly-read React SPA backed by a FastAPI JSON API visualizes consumption; a few write endpoints control plugs.
- `falk/config.py` + `falk/db.py` — shared config loader and lazy engine/session factory (reused by telemetry and the API; SQLite runs in WAL so the API reads while cron writes). Env overrides: `FALK_DEVICES_FILE`, `FALK_DATABASE_URI`.
- `falk/api/` — `main.py` (app factory + SPA mount), `routers/` (meters, plugs), `schemas.py` (pydantic v2), `aggregation.py` (time-series bucketing with `strftime`). Endpoints under `/api`: list/latest/timeseries for meters and plugs. The meter drives the gauges (total + L1/L2/L3) and per-phase series; plugs show per-appliance power/energy.
- Plug write endpoints: `POST /plugs/{id}/state` (immediate on/off) and boosts — `GET /plugs/boosts` (all active), `POST /plugs/{id}/boost` (`{on, duration_minutes}`: persists a `DeviceOverride` then actuates immediately, best-effort), `DELETE /plugs/{id}/boost`. Both reuse the `_actuate` helper. `until` is serialized as naive UTC, so the frontend counts down from `remaining_seconds` rather than parsing it.
- Time series: power = AVG per bucket; meter energy (kWh) = MAX−MIN of the cumulative Wh counter; plug energy is approximated as Σ power × sample-interval (plugs have no cumulative counter). Granularities: minute/hour/day/month with bucket-count guards.
- `frontend/` — Vite + React + TS + ECharts (gauges + series). Build output (`src/falk/api/static/`) is gitignored; build on deploy.
