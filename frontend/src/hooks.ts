import { useQuery } from "@tanstack/react-query";

import { api, type SeriesParams } from "./api/client";

const LATEST_POLL_MS = 60_000;

export function useMeters() {
  return useQuery({ queryKey: ["meters"], queryFn: api.listMeters });
}

export function useMeterLatest(meterId: number | undefined) {
  return useQuery({
    queryKey: ["meter-latest", meterId],
    queryFn: () => api.meterLatest(meterId!),
    enabled: meterId !== undefined,
    refetchInterval: LATEST_POLL_MS,
  });
}

export function useMeterBreakdown(meterId: number | undefined) {
  return useQuery({
    queryKey: ["meter-breakdown", meterId],
    queryFn: () => api.meterBreakdown(meterId!),
    enabled: meterId !== undefined,
    refetchInterval: LATEST_POLL_MS,
  });
}

export function useMeterSeries(
  meterId: number | undefined,
  params: SeriesParams,
) {
  return useQuery({
    queryKey: ["meter-series", meterId, params],
    queryFn: () => api.meterSeries(meterId!, params),
    enabled: meterId !== undefined,
  });
}

export function usePlugs() {
  return useQuery({ queryKey: ["plugs"], queryFn: api.listPlugs });
}

export function usePlugLatest(plugId: number | undefined) {
  return useQuery({
    queryKey: ["plug-latest", plugId],
    queryFn: () => api.plugLatest(plugId!),
    enabled: plugId !== undefined,
    refetchInterval: LATEST_POLL_MS,
  });
}

export function usePlugSeries(
  plugId: number | undefined,
  params: SeriesParams,
) {
  return useQuery({
    queryKey: ["plug-series", plugId, params],
    queryFn: () => api.plugSeries(plugId!, params),
    enabled: plugId !== undefined,
  });
}
