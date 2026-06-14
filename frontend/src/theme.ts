import type { PhaseSel } from "./api/types";

// Phosphor-green family: green-dominant, phases kept distinguishable but on-theme.
export const ACCENTS: Record<PhaseSel, string> = {
  total: "#00e676",
  l1: "#34d399",
  l2: "#a3e635",
  l3: "#2dd4bf",
};

// Green/teal family for devices; muted slate for the unassigned remainder.
export const DEVICE_PALETTE = [
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
export const UNASSIGNED_COLOR = "#3a4a44";
