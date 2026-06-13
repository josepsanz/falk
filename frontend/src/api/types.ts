// Mirror of the pydantic schemas in src/falk/api/schemas.py.

export type Metric = "power" | "energy";
export type Granularity = "minute" | "hour" | "day" | "month";
export type PhaseSel = "total" | "l1" | "l2" | "l3";

export interface Meter {
  id: number;
  name: string;
  brand: string;
  model: string;
  location: string | null;
  enabled: boolean;
}

export interface PhaseReading {
  name: string;
  act_power: number;
  current: number;
  voltage: number;
  pf: number;
}

export interface MeterLatest {
  meter_id: number;
  recorded_at: string;
  total_act_power: number;
  total_current: number;
  total_act_energy: number;
  phases: PhaseReading[];
}

export interface BreakdownDevice {
  id: number;
  name: string;
  power: number;
}

export interface Breakdown {
  meter_id: number;
  recorded_at: string;
  total_act_power: number;
  assigned: number;
  unassigned: number;
  devices: BreakdownDevice[];
}

export interface RankedDevice {
  id: number;
  name: string;
  value: number;
}

export interface Ranking {
  meter_id: number;
  metric: Metric;
  unit: string;
  window_days: number;
  total: number;
  unassigned: number;
  devices: RankedDevice[];
}

export interface Plug {
  id: number;
  name: string;
  brand: string;
  model: string;
  location: string | null;
  state: boolean;
  enabled: boolean;
}

export interface PlugLatest {
  plug_id: number;
  recorded_at: string;
  power: number;
  current: number;
  voltage: number;
}

export interface PlugState {
  plug_id: number;
  state: boolean;
}

export interface PlugStats {
  plug_id: number;
  window_days: number;
  samples: number;
  power_avg: number;
  power_min: number;
  power_max: number;
  power_median: number;
  power_p95: number;
  active_ratio: number;
  energy_total_kwh: number;
  energy_daily_avg_kwh: number;
  energy_today_kwh: number;
  energy_last7_kwh: number;
  forecast_next_day_kwh: number;
  forecast_next_30d_kwh: number;
  trend_pct: number | null;
}

export interface HeatmapCell {
  day: string;
  hour: number;
  value: number;
}

export interface Heatmap {
  plug_id: number;
  unit: string;
  days: string[];
  cells: HeatmapCell[];
}

export interface MeterStats {
  meter_id: number;
  window_days: number;
  samples: number;
  power_now: number;
  power_avg: number;
  power_min: number;
  power_max: number;
  power_median: number;
  power_p95: number;
  energy_total_kwh: number;
  energy_daily_avg_kwh: number;
  energy_today_kwh: number;
  energy_last7_kwh: number;
  forecast_next_day_kwh: number;
  forecast_next_30d_kwh: number;
  trend_pct: number | null;
}

export interface DeviceSeriesEntry {
  id: number;
  name: string;
  values: number[];
}

export interface DeviceSeries {
  meter_id: number;
  granularity: Granularity;
  unit: string;
  buckets: string[];
  devices: DeviceSeriesEntry[];
  unassigned: number[];
}

export interface CostPoint {
  bucket: string;
  energy_kwh: number | null;
  price_kwh: number | null;
  cost_eur: number | null;
}

export interface CostSeries {
  meter_id: number;
  granularity: Granularity;
  points: CostPoint[];
  total_energy_kwh: number;
  total_cost_eur: number;
  avg_price_kwh: number;
}

export interface TimeseriesPoint {
  bucket: string;
  value: number | null;
}

export interface Timeseries {
  metric: Metric;
  granularity: Granularity;
  unit: string;
  phase: PhaseSel | null;
  meter_id: number | null;
  plug_id: number | null;
  points: TimeseriesPoint[];
}
