import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";
import type { CostSeries, DeviceSeries } from "../api/types";
import { ACCENTS, DEVICE_PALETTE, UNASSIGNED_COLOR } from "../theme";

interface CostChartProps {
  series: CostSeries;
  valueKey: "energy_kwh" | "cost_eur";
  // Show only the hour (HH:00) on the x-axis — for single-day hourly views.
  hourOnly?: boolean;
  // Tint the area under the price line green→yellow→red by hourly price.
  colorByPrice?: boolean;
  // When provided, split each energy bar into a stacked per-device breakdown
  // (plus an "unassigned" slice) instead of a single aggregate bar.
  breakdown?: DeviceSeries;
}

const MONO = "JetBrains Mono, monospace";
const BAR_ACCENT = ACCENTS.total;
const PRICE_ACCENT = "#fbbf24";
const PRICE_AREA_ALPHA = 0.18;

// Cheap → expensive gradient stops, interpolated per hour.
const PRICE_CHEAP = [34, 197, 94]; // green
const PRICE_MID = [251, 191, 36]; // yellow
const PRICE_EXPENSIVE = [239, 68, 68]; // red

function hexToRgba(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function priceColor(norm: number, alpha: number): string {
  const t = Math.min(1, Math.max(0, norm));
  const [from, to, local] =
    t < 0.5
      ? [PRICE_CHEAP, PRICE_MID, t / 0.5]
      : [PRICE_MID, PRICE_EXPENSIVE, (t - 0.5) / 0.5];
  const channel = (i: number) => Math.round(from[i] + (to[i] - from[i]) * local);
  return `rgba(${channel(0)}, ${channel(1)}, ${channel(2)}, ${alpha})`;
}

function priceAreaGradient(prices: (number | null)[]) {
  const known = prices.filter((value): value is number => value != null);
  if (known.length === 0 || prices.length < 2) {
    return undefined;
  }
  const min = Math.min(...known);
  const range = Math.max(...known) - min || 1;
  const stops = prices.map((price, index) => ({
    offset: index / (prices.length - 1),
    color:
      price == null
        ? "rgba(0, 0, 0, 0)"
        : priceColor((price - min) / range, PRICE_AREA_ALPHA),
  }));
  return new echarts.graphic.LinearGradient(0, 0, 1, 0, stops);
}

const VALUE_META = {
  energy_kwh: { unit: "kWh", label: "Energia" },
  cost_eur: { unit: "€", label: "Cost" },
} as const;

// Align a device-series (its own bucket axis) onto the cost-series buckets, so a
// breakdown stays correct even when the cost series has been trimmed differently.
function alignDevices(series: CostSeries, breakdown: DeviceSeries) {
  const buckets = series.points.map((p) => p.bucket);
  const index = new Map(breakdown.buckets.map((b, i) => [b, i]));
  const pick = (values: number[]) =>
    buckets.map((b) => {
      const i = index.get(b);
      return i === undefined ? 0 : values[i];
    });
  const devices = breakdown.devices.map((d) => ({
    name: d.name,
    values: pick(d.values),
  }));
  const unassigned = pick(breakdown.unassigned);
  const hasUnassigned = unassigned.some((v) => v > 0);
  return { devices, unassigned, hasUnassigned };
}

export function CostChart({
  series,
  valueKey,
  hourOnly,
  colorByPrice,
  breakdown,
}: CostChartProps) {
  const { unit, label } = VALUE_META[valueKey];

  const option = useMemo(() => {
    const buckets = series.points.map((p) => p.bucket);
    const values = series.points.map((p) => p[valueKey]);
    const prices = series.points.map((p) => p.price_kwh);
    const priceArea = colorByPrice ? priceAreaGradient(prices) : undefined;

    const split = breakdown ? alignDevices(series, breakdown) : undefined;
    const barSeries = split
      ? [
          ...split.devices.map((d, i) => ({
            name: d.name,
            type: "bar" as const,
            stack: "energy",
            yAxisIndex: 0,
            data: d.values,
            itemStyle: { color: DEVICE_PALETTE[i % DEVICE_PALETTE.length] },
          })),
          ...(split.hasUnassigned
            ? [
                {
                  name: "Sense assignar",
                  type: "bar" as const,
                  stack: "energy",
                  yAxisIndex: 0,
                  data: split.unassigned,
                  itemStyle: {
                    color: UNASSIGNED_COLOR,
                    borderRadius: [3, 3, 0, 0] as [number, number, number, number],
                  },
                },
              ]
            : []),
        ]
      : [
          {
            name: label,
            type: "bar" as const,
            yAxisIndex: 0,
            data: values,
            itemStyle: { color: BAR_ACCENT, borderRadius: [3, 3, 0, 0] },
          },
        ];
    const legendData = split
      ? [
          ...split.devices.map((d) => d.name),
          ...(split.hasUnassigned ? ["Sense assignar"] : []),
          "Preu",
        ]
      : [label, "Preu"];

    return {
      textStyle: { fontFamily: MONO },
      grid: { left: 60, right: 56, top: 52, bottom: 60 },
      legend: {
        type: "scroll",
        data: legendData,
        top: 4,
        right: 8,
        textStyle: { color: "#6f8c80", fontFamily: MONO, fontSize: 10.5 },
        inactiveColor: "#3a4a42",
        pageIconColor: "#00e676",
        pageIconInactiveColor: "#3a4a44",
        pageTextStyle: { color: "#6f8c80", fontFamily: MONO },
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(4, 7, 10, 0.95)",
        borderColor: "rgba(0, 230, 118, 0.3)",
        borderWidth: 1,
        textStyle: { color: "#d6e9df", fontFamily: MONO, fontSize: 12 },
        formatter: (params: { axisValue: string; dataIndex: number }[]) => {
          const point = series.points[params[0]?.dataIndex ?? 0];
          if (!point) {
            return "";
          }
          const fmt = (v: number | null, suffix: string, digits: number) =>
            v == null ? "—" : `${v.toLocaleString("ca-ES", {
              minimumFractionDigits: digits,
              maximumFractionDigits: digits,
            })} ${suffix}`;
          const lines = [
            point.bucket,
            `Energia: ${fmt(point.energy_kwh, "kWh", 2)}`,
          ];
          if (split) {
            const idx = params[0]?.dataIndex ?? 0;
            for (let i = 0; i < split.devices.length; i++) {
              const d = split.devices[i];
              if (d.values[idx] > 0) {
                lines.push(`· ${d.name}: ${fmt(d.values[idx], "kWh", 2)}`);
              }
            }
            if (split.hasUnassigned && split.unassigned[idx] > 0) {
              lines.push(`· Sense assignar: ${fmt(split.unassigned[idx], "kWh", 2)}`);
            }
          }
          lines.push(
            `Preu: ${fmt(point.price_kwh, "€/kWh", 4)}`,
            `Cost: ${fmt(point.cost_eur, "€", 2)}`,
          );
          return lines.join("<br/>");
        },
      },
      xAxis: {
        type: "category",
        data: buckets,
        axisLine: { lineStyle: { color: "rgba(0, 230, 118, 0.18)" } },
        axisTick: { show: false },
        axisLabel: {
          color: "#6f8c80",
          fontFamily: MONO,
          fontSize: 10.5,
          hideOverlap: true,
          // Bucket is "YYYY-MM-DD HH:00:00"; show just "HH:00", but mark the day
          // change with the weekday so the two days don't blur together.
          formatter: hourOnly
            ? (value: string) => {
                const [date, time] = value.split(" ");
                const hm = time?.slice(0, 5) ?? value;
                if (hm !== "00:00") return hm;
                const [y, m, d] = date.split("-").map(Number);
                const wd = new Date(y, m - 1, d).toLocaleDateString("ca-ES", {
                  weekday: "short",
                });
                return `${wd} ${hm}`;
              }
            : undefined,
        },
      },
      yAxis: [
        {
          type: "value",
          name: unit,
          nameTextStyle: { color: "#44584e", fontFamily: MONO, fontSize: 10.5 },
          splitLine: { lineStyle: { color: "rgba(0, 230, 118, 0.07)" } },
          axisLabel: { color: "#6f8c80", fontFamily: MONO, fontSize: 10.5 },
        },
        {
          type: "value",
          name: "€/kWh",
          nameTextStyle: { color: "#7a6a3a", fontFamily: MONO, fontSize: 10.5 },
          splitLine: { show: false },
          axisLabel: { color: "#9a8a4a", fontFamily: MONO, fontSize: 10.5 },
        },
      ],
      dataZoom: [
        { type: "inside" },
        {
          type: "slider",
          height: 16,
          bottom: 18,
          borderColor: "transparent",
          backgroundColor: "rgba(0, 230, 118, 0.04)",
          fillerColor: "rgba(0, 230, 118, 0.12)",
          handleStyle: { color: BAR_ACCENT, borderColor: BAR_ACCENT },
          moveHandleStyle: { color: BAR_ACCENT },
          dataBackground: {
            lineStyle: { color: "rgba(0, 230, 118, 0.4)" },
            areaStyle: { color: "rgba(0, 230, 118, 0.08)" },
          },
          textStyle: { color: "#44584e", fontFamily: MONO },
        },
      ],
      series: [
        ...barSeries,
        {
          name: "Preu",
          type: "line",
          yAxisIndex: 1,
          data: prices,
          connectNulls: true,
          // The PVPC price is flat across each hour (e.g. 08:00–08:59) and jumps
          // at the boundary — a step function, not a smooth curve. "middle"
          // centres each flat segment on its hour slot, aligned with the bars.
          step: "middle",
          showSymbol: false,
          lineStyle: {
            width: 2,
            color: PRICE_ACCENT,
            shadowBlur: 8,
            shadowColor: hexToRgba(PRICE_ACCENT, 0.4),
          },
          itemStyle: { color: PRICE_ACCENT },
          areaStyle: priceArea ? { color: priceArea } : undefined,
        },
      ],
    };
  }, [series, valueKey, unit, label, hourOnly, colorByPrice, breakdown]);

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      notMerge
      style={{ height: 340, width: "100%" }}
      opts={{ renderer: "canvas" }}
    />
  );
}
