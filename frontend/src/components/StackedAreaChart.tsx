import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";
import type { DeviceSeries } from "../api/types";

const MONO = "JetBrains Mono, monospace";

// Green/teal family for devices; muted slate for the unassigned remainder.
const DEVICE_PALETTE = [
  "#00e676",
  "#34d399",
  "#2dd4bf",
  "#a3e635",
  "#22d3a5",
  "#5eead4",
  "#84cc16",
  "#10b981",
  "#4ade80",
];
const UNASSIGNED_COLOR = "#3a4a44";

function hexToRgba(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function areaSeries(name: string, data: number[], color: string) {
  return {
    name,
    type: "line" as const,
    stack: "total",
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 1, color },
    itemStyle: { color },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: hexToRgba(color, 0.55) },
        { offset: 1, color: hexToRgba(color, 0.1) },
      ]),
    },
    emphasis: { focus: "series" as const },
    data,
  };
}

export function StackedAreaChart({ series }: { series: DeviceSeries }) {
  const option = useMemo(() => {
    const deviceSeries = series.devices.map((device, index) =>
      areaSeries(
        device.name,
        device.values,
        DEVICE_PALETTE[index % DEVICE_PALETTE.length],
      ),
    );
    const hasUnassigned = series.unassigned.some((v) => v > 0);
    const allSeries = hasUnassigned
      ? [
          ...deviceSeries,
          areaSeries("Sense assignar", series.unassigned, UNASSIGNED_COLOR),
        ]
      : deviceSeries;

    return {
      textStyle: { fontFamily: MONO },
      grid: { left: 60, right: 22, top: 24, bottom: 78 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(4, 7, 10, 0.95)",
        borderColor: "rgba(0, 230, 118, 0.3)",
        borderWidth: 1,
        textStyle: { color: "#d6e9df", fontFamily: MONO, fontSize: 12 },
        valueFormatter: (v: number | null) =>
          v == null ? "—" : `${v.toLocaleString("ca-ES")} ${series.unit}`,
      },
      legend: {
        type: "scroll",
        bottom: 0,
        icon: "circle",
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: "#8aa89c", fontFamily: MONO, fontSize: 12 },
        pageTextStyle: { color: "#6f8c80", fontFamily: MONO },
        pageIconColor: "#00e676",
        pageIconInactiveColor: "#3a4a44",
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: series.buckets,
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
        axisLabel: { color: "#6f8c80", fontFamily: MONO, fontSize: 10.5 },
      },
      series: allSeries,
    };
  }, [series]);

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      notMerge
      style={{ height: 360, width: "100%" }}
      opts={{ renderer: "canvas" }}
    />
  );
}
