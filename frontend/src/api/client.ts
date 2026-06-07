import type {
  Breakdown,
  DeviceSeries,
  Granularity,
  Heatmap,
  Meter,
  MeterLatest,
  MeterStats,
  Metric,
  PhaseSel,
  Plug,
  PlugLatest,
  PlugState,
  PlugStats,
  Ranking,
  Timeseries,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path} → ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
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
  meterRanking: (id: number, metric: Metric, windowDays = 7) =>
    get<Ranking>(
      `/api/meters/${id}/ranking?metric=${metric}&window_days=${windowDays}`,
    ),
  meterSeries: (id: number, params: SeriesParams) =>
    get<Timeseries>(`/api/meters/${id}/timeseries?${seriesQuery(params)}`),
  meterDeviceSeries: (id: number, granularity: Granularity) =>
    get<DeviceSeries>(
      `/api/meters/${id}/device-series?granularity=${granularity}`,
    ),
  meterStats: (id: number, windowDays = 30) =>
    get<MeterStats>(`/api/meters/${id}/stats?window_days=${windowDays}`),
  listPlugs: () => get<Plug[]>("/api/plugs"),
  plugLatest: (id: number) => get<PlugLatest>(`/api/plugs/${id}/latest`),
  setPlugState: (id: number, on: boolean) =>
    post<PlugState>(`/api/plugs/${id}/state`, { on }),
  plugHeatmap: (id: number, days = 14) =>
    get<Heatmap>(`/api/plugs/${id}/heatmap?days=${days}`),
  plugStats: (id: number, windowDays = 30) =>
    get<PlugStats>(`/api/plugs/${id}/stats?window_days=${windowDays}`),
  plugSeries: (id: number, params: SeriesParams) =>
    get<Timeseries>(`/api/plugs/${id}/timeseries?${seriesQuery(params)}`),
};
