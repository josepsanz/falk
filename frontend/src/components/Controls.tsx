import type { Granularity, Metric, PhaseSel } from "../api/types";

interface SegmentedProps<T extends string> {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

export function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: SegmentedProps<T>) {
  return (
    <div className="control">
      <span className="control__label">{label}</span>
      <div className="segmented" role="group" aria-label={label}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={
              option.value === value ? "segmented__item is-active" : "segmented__item"
            }
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export const METRIC_OPTIONS: { value: Metric; label: string }[] = [
  { value: "power", label: "Potència (W)" },
  { value: "energy", label: "Energia (kWh)" },
];

export const GRANULARITY_OPTIONS: { value: Granularity; label: string }[] = [
  { value: "minute", label: "Minut" },
  { value: "hour", label: "Hora" },
  { value: "day", label: "Dia" },
  { value: "month", label: "Mes" },
];

export const PHASE_OPTIONS: { value: PhaseSel; label: string }[] = [
  { value: "total", label: "Total" },
  { value: "l1", label: "L1" },
  { value: "l2", label: "L2" },
  { value: "l3", label: "L3" },
];
