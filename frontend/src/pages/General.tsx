import { useState } from "react";

import type { Metric, PhaseSel } from "../api/types";
import { BreakdownChart } from "../components/BreakdownChart";
import { ConsumptionRanking } from "../components/ConsumptionRanking";
import { Gauge } from "../components/Gauge";
import { MeterStatsPanel } from "../components/MeterStatsPanel";
import { METRIC_OPTIONS, Segmented } from "../components/Controls";
import {
  useMeterBreakdown,
  useMeterLatest,
  useMeterRanking,
  useMeterStats,
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

const STATS_WINDOW_OPTIONS = [
  { value: "7", label: "7 dies" },
  { value: "30", label: "30 dies" },
  { value: "90", label: "90 dies" },
];

export function General() {
  const { settings } = useSettings();
  const { data: meters } = useMeters();
  const meterId = meters?.[0]?.id;

  const { data: latest } = useMeterLatest(meterId);
  const { data: breakdown } = useMeterBreakdown(meterId);

  const [rankMetric, setRankMetric] = useState<Metric>("power");
  const [rankWindow, setRankWindow] = useState(7);
  const { data: ranking } = useMeterRanking(meterId, rankMetric, rankWindow);

  const [statsWindow, setStatsWindow] = useState(30);
  const { data: stats } = useMeterStats(meterId, statsWindow);

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

      <div className="general-row">
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

        <section className="card stats-card">
          <div className="card-head card-head--row">
            <div>
              <span className="card-eyebrow">Estadístiques</span>
              <h2>Potència i consum</h2>
            </div>
            <Segmented
              label=""
              value={String(statsWindow)}
              options={STATS_WINDOW_OPTIONS}
              onChange={(value) => setStatsWindow(Number(value))}
            />
          </div>
          {stats ? (
            <MeterStatsPanel data={stats} />
          ) : (
            <div className="placeholder">Carregant estadístiques…</div>
          )}
        </section>
      </div>
    </div>
  );
}
