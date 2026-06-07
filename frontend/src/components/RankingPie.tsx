import ReactEChartsCore from "echarts-for-react/lib/core";
import { useMemo } from "react";

import echarts from "../charts/echarts";
import type { Ranking } from "../api/types";

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

interface Slice {
  name: string;
  value: number;
  itemStyle: { color: string };
}

interface TooltipParam {
  name: string;
  value: number;
  percent: number;
}

interface LabelParam {
  percent: number;
}

export function RankingPie({ data }: { data: Ranking }) {
  const option = useMemo(() => {
    const slices: Slice[] = data.devices
      .filter((device) => device.value > 0)
      .map((device, index) => ({
        name: device.name,
        value: Number(device.value.toFixed(3)),
        itemStyle: { color: DEVICE_PALETTE[index % DEVICE_PALETTE.length] },
      }));

    if (data.unassigned > 0) {
      slices.push({
        name: "Sense assignar",
        value: Number(data.unassigned.toFixed(3)),
        itemStyle: { color: UNASSIGNED_COLOR },
      });
    }

    const total = slices.reduce((sum, slice) => sum + slice.value, 0);

    return {
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(4, 7, 10, 0.95)",
        borderColor: "rgba(0, 230, 118, 0.3)",
        borderWidth: 1,
        textStyle: { color: "#d6e9df", fontFamily: MONO, fontSize: 12 },
        formatter: (p: TooltipParam) =>
          `${p.name}<br/>${p.value.toLocaleString("ca-ES")} ${data.unit} · ${p.percent}%`,
      },
      legend: {
        type: "scroll",
        orient: "vertical",
        right: 4,
        top: "middle",
        itemWidth: 11,
        itemHeight: 11,
        itemGap: 11,
        icon: "circle",
        textStyle: { color: "#8aa89c", fontFamily: MONO, fontSize: 13 },
        pageTextStyle: { color: "#6f8c80", fontFamily: MONO },
        pageIconColor: "#00e676",
        pageIconInactiveColor: "#3a4a44",
      },
      title: {
        text: total.toLocaleString("ca-ES", { maximumFractionDigits: 1 }),
        subtext: `${data.unit} · TOTAL`,
        left: "34%",
        top: "43%",
        textAlign: "center",
        textStyle: {
          color: "#eafff4",
          fontFamily: MONO,
          fontSize: 28,
          fontWeight: 700,
        },
        subtextStyle: { color: "#6f8c80", fontFamily: MONO, fontSize: 11 },
      },
      series: [
        {
          type: "pie",
          radius: ["56%", "82%"],
          center: ["34%", "52%"],
          avoidLabelOverlap: true,
          minAngle: 4,
          padAngle: 1.5,
          itemStyle: { borderColor: "#080d0b", borderWidth: 2, borderRadius: 3 },
          // Show the share inside slices large enough to fit the text.
          label: {
            show: true,
            position: "inside",
            color: "#06160f",
            fontFamily: MONO,
            fontSize: 11,
            fontWeight: 700,
            formatter: (p: LabelParam) =>
              p.percent >= 6 ? `${p.percent}%` : "",
          },
          labelLine: { show: false },
          emphasis: {
            scale: true,
            scaleSize: 5,
            itemStyle: {
              shadowBlur: 16,
              shadowColor: "rgba(0, 230, 118, 0.45)",
            },
          },
          data: slices,
        },
      ],
    };
  }, [data]);

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
