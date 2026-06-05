import { useEffect, useState } from "react";

import type { Granularity, Metric } from "../api/types";
import { TimeSeriesChart } from "../components/TimeSeriesChart";
import {
  GRANULARITY_OPTIONS,
  METRIC_OPTIONS,
  Segmented,
} from "../components/Controls";
import { usePlugLatest, usePlugSeries, usePlugs } from "../hooks";
import { ACCENTS } from "../theme";

export function Plugs() {
  const { data: plugs } = usePlugs();
  const [selected, setSelected] = useState<number | undefined>();

  useEffect(() => {
    if (selected === undefined && plugs?.length) {
      setSelected(plugs[0].id);
    }
  }, [plugs, selected]);

  const { data: latest } = usePlugLatest(selected);
  const [metric, setMetric] = useState<Metric>("power");
  const [granularity, setGranularity] = useState<Granularity>("hour");
  const { data: series } = usePlugSeries(selected, { metric, granularity });

  // Energy can't be resolved finer than the sampling interval.
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
          <h1>Endolls</h1>
          <p className="muted">Consum per aparell</p>
        </div>
      </header>

      <div className="plugs-layout">
        <aside className="card plug-list">
          {(plugs ?? []).map((plug) => (
            <button
              key={plug.id}
              type="button"
              className={
                plug.id === selected ? "plug-item is-active" : "plug-item"
              }
              onClick={() => setSelected(plug.id)}
            >
              <span className="plug-item__name">{plug.name}</span>
              <span className={plug.state ? "dot dot--on" : "dot"} />
            </button>
          ))}
        </aside>

        <section className="card series-card">
          <div className="plug-head">
            <h2>{plugs?.find((p) => p.id === selected)?.name ?? "—"}</h2>
            {latest && (
              <div className="plug-stats">
                <span>
                  <strong>{Math.round(latest.power)}</strong> W
                </span>
                <span>
                  <strong>{(latest.current / 1000).toFixed(2)}</strong> A
                </span>
                <span>
                  <strong>{Math.round(latest.voltage)}</strong> V
                </span>
              </div>
            )}
          </div>
          <div className="controls">
            <Segmented
              label="Mètrica"
              value={metric}
              options={METRIC_OPTIONS}
              onChange={handleMetric}
            />
            <Segmented
              label="Granularitat"
              value={granularity}
              options={granularityOptions}
              onChange={setGranularity}
            />
          </div>
          {series ? (
            <TimeSeriesChart series={series} accent={ACCENTS.l2} />
          ) : (
            <div className="placeholder">Carregant sèrie…</div>
          )}
        </section>
      </div>
    </div>
  );
}
