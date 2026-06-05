import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";
import type { Heatmap } from "../api/types";

const MONO = "JetBrains Mono, monospace";

interface HeatmapTooltipParam {
  value: [number, number, number];
}

function formatDay(iso: string): string {
  // "YYYY-MM-DD" -> "DD/MM"
  const [, month, day] = iso.split("-");
  return `${day}/${month}`;
}

export function PlugHeatmap({ data }: { data: Heatmap }) {
  const hours = useMemo(
    () => Array.from({ length: 24 }, (_, hour) => `${hour}`),
    [],
  );

  const option = useMemo(() => {
    const dayIndex = new Map(data.days.map((day, index) => [day, index]));
    const cells = data.cells.map((cell) => [
      cell.hour,
      dayIndex.get(cell.day) ?? 0,
      Math.round(cell.value),
    ]);
    const maxValue = Math.max(...data.cells.map((cell) => cell.value), 1);
    const dayLabels = data.days.map(formatDay);

    return {
      tooltip: {
        position: "top",
        backgroundColor: "rgba(4, 7, 10, 0.95)",
        borderColor: "rgba(0, 230, 118, 0.3)",
        borderWidth: 1,
        textStyle: { color: "#d6e9df", fontFamily: MONO, fontSize: 12 },
        formatter: (p: HeatmapTooltipParam) =>
          `${dayLabels[p.value[1]]} · ${p.value[0]}h<br/>${p.value[2]} ${data.unit}`,
      },
      grid: { left: 58, right: 16, top: 12, bottom: 64 },
      xAxis: {
        type: "category",
        data: hours,
        splitArea: { show: false },
        axisLine: { lineStyle: { color: "rgba(0, 230, 118, 0.18)" } },
        axisTick: { show: false },
        axisLabel: { color: "#6f8c80", fontFamily: MONO, fontSize: 10 },
      },
      yAxis: {
        type: "category",
        data: dayLabels,
        splitArea: { show: false },
        axisLine: { lineStyle: { color: "rgba(0, 230, 118, 0.18)" } },
        axisTick: { show: false },
        axisLabel: { color: "#6f8c80", fontFamily: MONO, fontSize: 10 },
      },
      visualMap: {
        min: 0,
        max: maxValue,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 8,
        itemWidth: 12,
        itemHeight: 120,
        inRange: {
          color: ["#06251a", "#0a7d46", "#10b981", "#34d399", "#bbf7d0"],
        },
        textStyle: { color: "#6f8c80", fontFamily: MONO, fontSize: 10 },
      },
      series: [
        {
          type: "heatmap",
          data: cells,
          itemStyle: { borderColor: "#080d0b", borderWidth: 1, borderRadius: 2 },
          emphasis: {
            itemStyle: { shadowBlur: 8, shadowColor: "rgba(0, 230, 118, 0.6)" },
          },
        },
      ],
    };
  }, [data, hours]);

  const height = Math.max(220, data.days.length * 26 + 110);

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      notMerge
      style={{ height, width: "100%" }}
      opts={{ renderer: "canvas" }}
    />
  );
}
