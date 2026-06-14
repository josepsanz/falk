import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type SeriesParams } from "./api/client";
import type { Granularity } from "./api/types";

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

export function useMeterRanking(
  meterId: number | undefined,
  metric: "power" | "energy",
  windowDays: number,
) {
  return useQuery({
    queryKey: ["meter-ranking", meterId, metric, windowDays],
    queryFn: () => api.meterRanking(meterId!, metric, windowDays),
    enabled: meterId !== undefined,
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

export function useMeterStats(
  meterId: number | undefined,
  windowDays: number,
) {
  return useQuery({
    queryKey: ["meter-stats", meterId, windowDays],
    queryFn: () => api.meterStats(meterId!, windowDays),
    enabled: meterId !== undefined,
  });
}

export function useMeterCostSeries(
  meterId: number | undefined,
  granularity: Granularity,
  from?: string,
  to?: string,
) {
  return useQuery({
    queryKey: ["meter-cost-series", meterId, granularity, from, to],
    queryFn: () => api.meterCostSeries(meterId!, granularity, from, to),
    enabled: meterId !== undefined,
  });
}

export function useMeterDeviceSeries(
  meterId: number | undefined,
  granularity: Granularity,
) {
  return useQuery({
    queryKey: ["meter-device-series", meterId, granularity],
    queryFn: () => api.meterDeviceSeries(meterId!, granularity),
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

export function usePlugStats(plugId: number | undefined) {
  return useQuery({
    queryKey: ["plug-stats", plugId],
    queryFn: () => api.plugStats(plugId!),
    enabled: plugId !== undefined,
  });
}

export function usePlugHeatmap(plugId: number | undefined) {
  return useQuery({
    queryKey: ["plug-heatmap", plugId],
    queryFn: () => api.plugHeatmap(plugId!),
    enabled: plugId !== undefined,
  });
}

export function useSetPlugState() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, on }: { id: number; on: boolean }) =>
      api.setPlugState(id, on),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugs"] });
    },
  });
}

export function useBoosts() {
  return useQuery({
    queryKey: ["boosts"],
    queryFn: api.listBoosts,
    refetchInterval: 30_000,
  });
}

function useBoostMutation<TArgs>(mutationFn: (args: TArgs) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugs"] });
      queryClient.invalidateQueries({ queryKey: ["boosts"] });
    },
  });
}

export function useStartBoost() {
  return useBoostMutation(
    ({
      id,
      on,
      durationMinutes,
    }: {
      id: number;
      on: boolean;
      durationMinutes: number;
    }) => api.startBoost(id, on, durationMinutes),
  );
}

export function useClearBoost() {
  return useBoostMutation(({ id }: { id: number }) => api.clearBoost(id));
}
