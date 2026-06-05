import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";

interface GaugeProps {
  value: number;
  max: number;
  label: string;
  unit: string;
  size?: "large" | "small";
  accent?: string;
}

const ACCENT_DEFAULT = "#00e676";
const MONO = "JetBrains Mono, monospace";

export function Gauge({
  value,
  max,
  label,
  unit,
  size = "small",
  accent = ACCENT_DEFAULT,
}: GaugeProps) {
  const large = size === "large";

  const option = useMemo(
    () => ({
      series: [
        {
          type: "gauge",
          startAngle: 220,
          endAngle: -40,
          min: 0,
          max,
          radius: "94%",
          progress: {
            show: true,
            width: large ? 16 : 11,
            roundCap: true,
            itemStyle: {
              color: accent,
              shadowBlur: large ? 18 : 12,
              shadowColor: accent,
            },
          },
          pointer: {
            length: "60%",
            width: large ? 5 : 3,
            itemStyle: { color: accent },
          },
          axisLine: {
            roundCap: true,
            lineStyle: {
              width: large ? 16 : 11,
              color: [[1, "rgba(0, 230, 118, 0.09)"]],
            },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          anchor: {
            show: true,
            size: large ? 12 : 8,
            itemStyle: { color: accent },
          },
          // Name and figure stacked in the lower-centre gap of the meter.
          title: {
            offsetCenter: [0, large ? "58%" : "62%"],
            fontSize: large ? 14 : 12,
            fontFamily: MONO,
            color: "#8aa89c",
            fontWeight: 500,
            // letterSpacing isn't supported; rely on uppercase + size.
          },
          detail: {
            valueAnimation: true,
            offsetCenter: [0, large ? "82%" : "86%"],
            fontSize: large ? 46 : 23,
            fontFamily: MONO,
            fontWeight: 700,
            color: "#d6e9df",
            formatter: (raw: number) =>
              `{value|${Math.round(raw).toLocaleString("ca-ES")}}{unit| ${unit}}`,
            rich: {
              value: {
                fontSize: large ? 46 : 23,
                fontFamily: MONO,
                fontWeight: 700,
                color: "#eafff4",
              },
              unit: {
                fontSize: large ? 16 : 11,
                fontFamily: MONO,
                color: "#6f8c80",
                padding: [0, 0, large ? 8 : 3, 3],
              },
            },
          },
          data: [{ value, name: label.toUpperCase() }],
        },
      ],
    }),
    [value, max, label, unit, large, accent],
  );

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      notMerge
      style={{ height: large ? 384 : 188, width: "100%" }}
      opts={{ renderer: "canvas" }}
    />
  );
}
