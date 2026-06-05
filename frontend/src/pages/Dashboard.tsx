import { useState } from "react";

import type { Granularity, Metric, PhaseSel } from "../api/types";
import { BreakdownChart } from "../components/BreakdownChart";
import { ConsumptionRanking } from "../components/ConsumptionRanking";
import { Gauge } from "../components/Gauge";
import { TimeSeriesChart } from "../components/TimeSeriesChart";
import {
  GRANULARITY_OPTIONS,
  METRIC_OPTIONS,
  PHASE_OPTIONS,
  Segmented,
} from "../components/Controls";
import {
  useMeterBreakdown,
  useMeterLatest,
  useMeterRanking,
  useMeterSeries,
  useMeters,
} from "../hooks";
import { useSettings } from "../settings";
import { ACCENTS } from "../theme";

const PHASE_LABELS: Record<string, string> = {
  l1: "Fase L1",
  l2: "Fase L2",
  l3: "Fase L3",
};

const RANK_WINDOW_OPTIONS = [
  { value: "1", label: "Avui" },
  { value: "7", label: "7 dies" },
  { value: "30", label: "30 dies" },
];

export function Dashboard() {
  const { settings } = useSettings();
  const { data: meters } = useMeters();
  const meterId = meters?.[0]?.id;

  const { data: latest } = useMeterLatest(meterId);
  const { data: breakdown } = useMeterBreakdown(meterId);

  const [rankMetric, setRankMetric] = useState<Metric>("power");
  const [rankWindow, setRankWindow] = useState(7);
  const { data: ranking } = useMeterRanking(meterId, rankMetric, rankWindow);

  const [metric, setMetric] = useState<Metric>("power");
  const [granularity, setGranularity] = useState<Granularity>("hour");
  const [phase, setPhase] = useState<PhaseSel>("total");
  const { data: series } = useMeterSeries(meterId, {
    metric,
    granularity,
    phase,
  });

  // Energy can't be resolved finer than the sampling interval, so minute
  // granularity is unavailable for energy.
  const granularityOptions =
    metric === "energy"
      ? GRANULARITY_OPTIONS.filter((option) => option.value !== "minute")
      : GRANULARITY_OPTIONS;

  const handleMetric = (next: Metric) => {
    setMetric(next);
    if (next === "energy" && granularity === "minute") {
      setGranularity("hour");
    }
  };

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <h1>Consum elèctric</h1>
          <p className="muted">{meters?.[0]?.name ?? "—"}</p>
        </div>
        {latest && (
          <span className="timestamp">
            Actualitzat{" "}
            {new Date(latest.recorded_at).toLocaleString("ca-ES", {
              hour: "2-digit",
              minute: "2-digit",
              day: "2-digit",
              month: "short",
            })}
          </span>
        )}
      </header>

      <section className="hero-row">
        <div className="card gauge-card gauge-card--total">
          <Gauge
            value={latest?.total_act_power ?? 0}
            max={settings.gaugeTotalMax}
            label="Consum total"
            unit="W"
            size="large"
            accent={ACCENTS.total}
          />
        </div>
        <div className="card breakdown-card">
          <div className="card-head">
            <span className="card-eyebrow">Desglossament</span>
            <h2>Consum per dispositiu</h2>
          </div>
          {breakdown ? (
            <BreakdownChart data={breakdown} />
          ) : (
            <div className="placeholder">Carregant desglossament…</div>
          )}
        </div>
      </section>

      <section className="gauge-card__phases">
        {(latest?.phases ?? []).map((phaseReading) => (
          <div className="card gauge-card" key={phaseReading.name}>
            <Gauge
              value={phaseReading.act_power}
              max={settings.gaugePhaseMax}
              label={PHASE_LABELS[phaseReading.name] ?? phaseReading.name}
              unit="W"
              accent={ACCENTS[phaseReading.name as PhaseSel] ?? ACCENTS.total}
            />
          </div>
        ))}
      </section>

      <section className="card ranking-card">
        <div className="card-head card-head--row">
          <div>
            <span className="card-eyebrow">Rànquing</span>
            <h2>Qui consumeix més</h2>
          </div>
          <div className="ranking-controls">
            <Segmented
              label=""
              value={rankMetric}
              options={METRIC_OPTIONS}
              onChange={setRankMetric}
            />
            {rankMetric === "energy" && (
              <Segmented
                label=""
                value={String(rankWindow)}
                options={RANK_WINDOW_OPTIONS}
                onChange={(value) => setRankWindow(Number(value))}
              />
            )}
          </div>
        </div>
        {ranking ? (
          <ConsumptionRanking data={ranking} />
        ) : (
          <div className="placeholder">Carregant rànquing…</div>
        )}
      </section>

      <section className="card series-card">
        <div className="controls">
          <Segmented
            label="Mètrica"
            value={metric}
            options={METRIC_OPTIONS}
            onChange={handleMetric}
          />
          <Segmented
            label="Fase"
            value={phase}
            options={PHASE_OPTIONS}
            onChange={setPhase}
          />
          <Segmented
            label="Granularitat"
            value={granularity}
            options={granularityOptions}
            onChange={setGranularity}
          />
        </div>
        {series ? (
          <TimeSeriesChart series={series} accent={ACCENTS[phase]} />
        ) : (
          <div className="placeholder">Carregant sèrie…</div>
        )}
      </section>
    </div>
  );
}
