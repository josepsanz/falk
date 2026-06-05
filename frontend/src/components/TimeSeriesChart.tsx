import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";
import type { Metric, Timeseries } from "../api/types";

interface TimeSeriesChartProps {
  series: Timeseries;
  accent?: string;
}

const ACCENT_DEFAULT = "#00e676";
const MONO = "JetBrains Mono, monospace";

function chartType(metric: Metric): "line" | "bar" {
  // Power is a continuous quantity (line); energy is consumption per bucket (bar).
  return metric === "power" ? "line" : "bar";
}

function hexToRgba(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function TimeSeriesChart({
  series,
  accent = ACCENT_DEFAULT,
}: TimeSeriesChartProps) {
  const isLine = chartType(series.metric) === "line";

  const option = useMemo(
    () => ({
      textStyle: { fontFamily: MONO },
      grid: { left: 60, right: 22, top: 24, bottom: 60 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(4, 7, 10, 0.95)",
        borderColor: "rgba(0, 230, 118, 0.3)",
        borderWidth: 1,
        textStyle: { color: "#d6e9df", fontFamily: MONO, fontSize: 12 },
        valueFormatter: (v: number | null) =>
          v == null ? "—" : `${v.toLocaleString("ca-ES")} ${series.unit}`,
      },
      xAxis: {
        type: "category",
        data: series.points.map((p) => p.bucket),
        boundaryGap: !isLine,
        axisLine: { lineStyle: { color: "rgba(0, 230, 118, 0.18)" } },
        axisTick: { show: false },
        axisLabel: {
          color: "#6f8c80",
          fontFamily: MONO,
          fontSize: 10.5,
          hideOverlap: true,
        },
      },
      yAxis: {
        type: "value",
        name: series.unit,
        nameTextStyle: { color: "#44584e", fontFamily: MONO, fontSize: 10.5 },
        splitLine: { lineStyle: { color: "rgba(0, 230, 118, 0.07)" } },
        axisLabel: {
          color: "#6f8c80",
          fontFamily: MONO,
          fontSize: 10.5,
        },
      },
      dataZoom: [
        { type: "inside" },
        {
          type: "slider",
          height: 16,
          bottom: 18,
          borderColor: "transparent",
          backgroundColor: "rgba(0, 230, 118, 0.04)",
          fillerColor: "rgba(0, 230, 118, 0.12)",
          handleStyle: { color: accent, borderColor: accent },
          moveHandleStyle: { color: accent },
          dataBackground: {
            lineStyle: { color: "rgba(0, 230, 118, 0.4)" },
            areaStyle: { color: "rgba(0, 230, 118, 0.08)" },
          },
          textStyle: { color: "#44584e", fontFamily: MONO },
        },
      ],
      series: [
        {
          type: chartType(series.metric),
          data: series.points.map((p) => p.value),
          connectNulls: isLine,
          smooth: isLine,
          showSymbol: false,
          itemStyle: {
            color: accent,
            borderRadius: isLine ? 0 : [3, 3, 0, 0],
          },
          areaStyle: isLine
            ? {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: hexToRgba(accent, 0.38) },
                  { offset: 1, color: hexToRgba(accent, 0.01) },
                ]),
              }
            : undefined,
          lineStyle: isLine
            ? {
                width: 2,
                color: accent,
                shadowBlur: 12,
                shadowColor: hexToRgba(accent, 0.5),
              }
            : undefined,
        },
      ],
    }),
    [series, accent, isLine],
  );

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
