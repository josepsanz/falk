import { hierarchy } from "d3-hierarchy";
import { polygonArea, polygonCentroid } from "d3-polygon";
import { voronoiTreemap } from "d3-voronoi-treemap";
import { useMemo } from "react";

import type { Ranking } from "../api/types";

const MONO = "JetBrains Mono, monospace";
const SIZE = 360;
const RADIUS = 172;

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

// Below this polygon area (px²) a cell is too small to label legibly.
const LABEL_AREA_MIN = 1300;

interface Leaf {
  name: string;
  value: number;
  color: string;
  text: string;
}

interface TreeNode {
  value?: number;
  children?: Leaf[];
}

type Point = [number, number];

// Deterministic PRNG so the layout stays stable across re-renders (the voronoi
// solver seeds initial cell positions randomly otherwise).
function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function circleClip(cx: number, cy: number, r: number, n: number): Point[] {
  const points: Point[] = [];
  for (let i = 0; i < n; i += 1) {
    const angle = (2 * Math.PI * i) / n;
    points.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
  }
  return points;
}

export function ConvexTreemap({ data }: { data: Ranking }) {
  const cells = useMemo(() => {
    const entries = data.devices
      .filter((device) => device.value > 0)
      .map((device, index) => ({
        name: device.name,
        value: device.value,
        color: DEVICE_PALETTE[index % DEVICE_PALETTE.length],
      }));
    if (data.unassigned > 0) {
      entries.push({
        name: "Sense assignar",
        value: data.unassigned,
        color: UNASSIGNED_COLOR,
      });
    }
    if (entries.length === 0) {
      return [];
    }

    const total = entries.reduce((sum, e) => sum + e.value, 0) || 1;
    const leaves: Leaf[] = entries.map((e) => ({
      ...e,
      text: `${e.value.toLocaleString("ca-ES")} ${data.unit} · ${(
        (e.value / total) *
        100
      ).toFixed(1)}%`,
    }));

    const root = hierarchy<TreeNode>({ children: leaves }).sum(
      (node) => node.value ?? 0,
    );
    voronoiTreemap()
      .clip(circleClip(SIZE / 2, SIZE / 2, RADIUS, 80))
      .prng(mulberry32(0x9e3779b9))(root);

    return root.leaves().map((leaf) => {
      const polygon = (leaf as unknown as { polygon: Point[] }).polygon;
      const [cx, cy] = polygonCentroid(polygon);
      const area = Math.abs(polygonArea(polygon));
      return {
        leaf: leaf.data as unknown as Leaf,
        points: polygon.map((p) => p.join(",")).join(" "),
        cx,
        cy,
        showLabel: area >= LABEL_AREA_MIN,
      };
    });
  }, [data]);

  if (cells.length === 0) {
    return <div className="placeholder">Sense dades de consum.</div>;
  }

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      style={{ width: "100%", height: 360 }}
      role="img"
      aria-label="Consum per dispositiu (treemap convex)"
    >
      {cells.map(({ leaf, points, cx, cy, showLabel }) => (
        <g key={leaf.name} className="treemap-cell">
          <polygon
            points={points}
            fill={leaf.color}
            fillOpacity={0.82}
            stroke="#080d0b"
            strokeWidth={2}
            strokeLinejoin="round"
          >
            <title>{`${leaf.name} · ${leaf.text}`}</title>
          </polygon>
          {showLabel && (
            <text
              x={cx}
              y={cy}
              textAnchor="middle"
              fontFamily={MONO}
              pointerEvents="none"
              fill={leaf.color === UNASSIGNED_COLOR ? "#cfe6dc" : "#06160f"}
            >
              <tspan x={cx} fontSize={12} fontWeight={700}>
                {leaf.name}
              </tspan>
              <tspan x={cx} dy={15} fontSize={10.5}>
                {leaf.text}
              </tspan>
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}
