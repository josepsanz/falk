import type {
  Breakdown,
  Granularity,
  Meter,
  MeterLatest,
  Metric,
  PhaseSel,
  Plug,
  PlugLatest,
  Timeseries,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path} → ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface SeriesParams {
  metric: Metric;
  granularity: Granularity;
  phase?: PhaseSel;
}

function seriesQuery({ metric, granularity, phase }: SeriesParams): string {
  const params = new URLSearchParams({ metric, granularity });
  if (phase) {
    params.set("phase", phase);
  }
  return params.toString();
}

export const api = {
  listMeters: () => get<Meter[]>("/api/meters"),
  meterLatest: (id: number) => get<MeterLatest>(`/api/meters/${id}/latest`),
  meterBreakdown: (id: number) => get<Breakdown>(`/api/meters/${id}/breakdown`),
  meterSeries: (id: number, params: SeriesParams) =>
    get<Timeseries>(`/api/meters/${id}/timeseries?${seriesQuery(params)}`),
  listPlugs: () => get<Plug[]>("/api/plugs"),
  plugLatest: (id: number) => get<PlugLatest>(`/api/plugs/${id}/latest`),
  plugSeries: (id: number, params: SeriesParams) =>
    get<Timeseries>(`/api/plugs/${id}/timeseries?${seriesQuery(params)}`),
};
