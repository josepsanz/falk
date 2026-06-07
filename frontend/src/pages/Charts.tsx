import { useState } from "react";

import type { Granularity, Metric, PhaseSel } from "../api/types";
import { ConvexTreemap } from "../components/ConvexTreemap";
import { RankingPie } from "../components/RankingPie";
import { StackedAreaChart } from "../components/StackedAreaChart";
import { TimeSeriesChart } from "../components/TimeSeriesChart";
import {
  GRANULARITY_OPTIONS,
  METRIC_OPTIONS,
  PHASE_OPTIONS,
  Segmented,
} from "../components/Controls";
import {
  useMeterDeviceSeries,
  useMeterRanking,
  useMeterSeries,
  useMeters,
} from "../hooks";
import { ACCENTS } from "../theme";

// Energy can only be resolved down to the sampling interval, so minute
// granularity is excluded for the energy-based charts.
const ENERGY_GRANULARITY_OPTIONS = GRANULARITY_OPTIONS.filter(
  (option) => option.value !== "minute",
);

const RANK_WINDOW_OPTIONS = [
  { value: "1", label: "Avui" },
  { value: "7", label: "7 dies" },
  { value: "30", label: "30 dies" },
];

export function Charts() {
  const { data: meters } = useMeters();
  const meterId = meters?.[0]?.id;

  const [metric, setMetric] = useState<Metric>("power");
  const [granularity, setGranularity] = useState<Granularity>("hour");
  const [phase, setPhase] = useState<PhaseSel>("total");
  const { data: series } = useMeterSeries(meterId, {
    metric,
    granularity,
    phase,
  });

  const granularityOptions =
    metric === "energy" ? ENERGY_GRANULARITY_OPTIONS : GRANULARITY_OPTIONS;

  const handleMetric = (next: Metric) => {
    setMetric(next);
    if (next === "energy" && granularity === "minute") {
      setGranularity("hour");
    }
  };

  const [stackGranularity, setStackGranularity] = useState<Granularity>("day");
  const { data: deviceSeries } = useMeterDeviceSeries(meterId, stackGranularity);

  const [treemapWindow, setTreemapWindow] = useState(30);
  const { data: ranking } = useMeterRanking(meterId, "energy", treemapWindow);

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <h1>Charts</h1>
          <p className="muted">{meters?.[0]?.name ?? "—"}</p>
        </div>
      </header>

      <section className="card series-card">
        <div className="card-head">
          <span className="card-eyebrow">Sèrie temporal</span>
          <h2>Evolució del consum</h2>
        </div>
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

      <section className="card series-card">
        <div className="card-head card-head--row">
          <div>
            <span className="card-eyebrow">Acumulat</span>
            <h2>Energia per dispositiu</h2>
          </div>
          <Segmented
            label=""
            value={stackGranularity}
            options={ENERGY_GRANULARITY_OPTIONS}
            onChange={setStackGranularity}
          />
        </div>
        {deviceSeries ? (
          <StackedAreaChart series={deviceSeries} />
        ) : (
          <div className="placeholder">Carregant consum per dispositiu…</div>
        )}
      </section>

      <div className="charts-row">
        <section className="card breakdown-card">
          <div className="card-head card-head--row">
            <div>
              <span className="card-eyebrow">Repartiment</span>
              <h2>Treemap de consum</h2>
            </div>
            <Segmented
              label=""
              value={String(treemapWindow)}
              options={RANK_WINDOW_OPTIONS}
              onChange={(value) => setTreemapWindow(Number(value))}
            />
          </div>
          {ranking ? (
            <ConvexTreemap data={ranking} />
          ) : (
            <div className="placeholder">Carregant treemap…</div>
          )}
        </section>

        <section className="card breakdown-card">
          <div className="card-head">
            <span className="card-eyebrow">Repartiment</span>
            <h2>Pastís de consum</h2>
          </div>
          {ranking ? (
            <RankingPie data={ranking} />
          ) : (
            <div className="placeholder">Carregant pastís…</div>
          )}
        </section>
      </div>
    </div>
  );
}
