import { useEffect, useState } from "react";

import type { PlugBoost } from "../api/types";
import { useClearBoost, useStartBoost } from "../hooks";

const DURATION_PRESETS = [30, 60, 120, 180];

// Count down from the server-provided remaining seconds rather than parsing
// `until`: the backend serializes it as a naive UTC timestamp, which the
// browser would otherwise misread as local time.
function useCountdown(remainingSeconds: number | undefined): number {
  const [remaining, setRemaining] = useState(remainingSeconds ?? 0);

  useEffect(() => {
    setRemaining(remainingSeconds ?? 0);
  }, [remainingSeconds]);

  useEffect(() => {
    if (!remainingSeconds) {
      return;
    }
    const timer = setInterval(() => {
      setRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [remainingSeconds]);

  return remaining;
}

function formatRemaining(total: number): string {
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
  }
  return `${seconds}s`;
}

function formatPreset(minutes: number): string {
  return minutes % 60 === 0 ? `${minutes / 60}h` : `${minutes}m`;
}

interface BoostControlProps {
  plugId: number;
  boost: PlugBoost | undefined;
}

export function BoostControl({ plugId, boost }: BoostControlProps) {
  const startBoost = useStartBoost();
  const clearBoost = useClearBoost();
  const [on, setOn] = useState(true);
  const [minutes, setMinutes] = useState(60);
  const remaining = useCountdown(boost?.remaining_seconds);

  if (boost && remaining > 0) {
    return (
      <div className="boost boost--active">
        <span className="boost__eyebrow">Boost</span>
        <span
          className={
            boost.desired_state
              ? "boost__badge boost__badge--on"
              : "boost__badge boost__badge--off"
          }
        >
          {boost.desired_state ? "Encès" : "Apagat"}
        </span>
        <span className="boost__countdown">{formatRemaining(remaining)} restants</span>
        <button
          type="button"
          className="boost__btn boost__btn--clear"
          disabled={clearBoost.isPending}
          onClick={() => clearBoost.mutate({ id: plugId })}
        >
          Cancel·lar
        </button>
      </div>
    );
  }

  return (
    <div className="boost">
      <span className="boost__eyebrow">Boost manual</span>
      <div className="segmented" role="group" aria-label="Direcció del boost">
        <button
          type="button"
          className={on ? "segmented__item is-active" : "segmented__item"}
          onClick={() => setOn(true)}
        >
          ON
        </button>
        <button
          type="button"
          className={!on ? "segmented__item is-active" : "segmented__item"}
          onClick={() => setOn(false)}
        >
          OFF
        </button>
      </div>
      <div className="segmented" role="group" aria-label="Durada del boost">
        {DURATION_PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            className={
              preset === minutes ? "segmented__item is-active" : "segmented__item"
            }
            onClick={() => setMinutes(preset)}
          >
            {formatPreset(preset)}
          </button>
        ))}
      </div>
      <input
        type="number"
        className="boost__minutes"
        min={1}
        max={1440}
        value={minutes}
        aria-label="Minuts personalitzats"
        onChange={(event) => setMinutes(Number(event.target.value))}
      />
      <span className="boost__unit">min</span>
      <button
        type="button"
        className="boost__btn"
        disabled={startBoost.isPending || minutes < 1 || minutes > 1440}
        onClick={() =>
          startBoost.mutate({ id: plugId, on, durationMinutes: minutes })
        }
      >
        Activar
      </button>
      {startBoost.isError && (
        <p className="error-text">No s'ha pogut activar el boost.</p>
      )}
    </div>
  );
}
