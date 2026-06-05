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
