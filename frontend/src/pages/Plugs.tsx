import { useEffect, useState } from "react";

import type { Granularity, Metric } from "../api/types";
import { BoostControl } from "../components/BoostControl";
import { PlugHeatmap } from "../components/PlugHeatmap";
import { PlugStatsPanel } from "../components/PlugStatsPanel";
import { TimeSeriesChart } from "../components/TimeSeriesChart";
import {
  GRANULARITY_OPTIONS,
  METRIC_OPTIONS,
  Segmented,
} from "../components/Controls";
import {
  useBoosts,
  usePlugHeatmap,
  usePlugLatest,
  usePlugSeries,
  usePlugStats,
  usePlugs,
  useSetPlugState,
} from "../hooks";
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
  const { data: boosts } = useBoosts();
  const setPlugState = useSetPlugState();
  const selectedPlug = plugs?.find((plug) => plug.id === selected);
  const boostFor = (plugId: number) =>
    boosts?.find(
      (boost) => boost.plug_id === plugId && boost.remaining_seconds > 0,
    );
  const [metric, setMetric] = useState<Metric>("power");
  const [granularity, setGranularity] = useState<Granularity>("hour");
  const { data: series } = usePlugSeries(selected, { metric, granularity });
  const { data: heatmap } = usePlugHeatmap(selected);
  const { data: stats } = usePlugStats(selected);

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
              {boostFor(plug.id) && (
                <span className="boost-tag" title="Boost actiu">
                  ⚡
                </span>
              )}
              <span className={plug.state ? "dot dot--on" : "dot"} />
            </button>
          ))}
        </aside>

        <div className="plug-main">
          <section className="card series-card">
          <div className="plug-head">
            <h2>{selectedPlug?.name ?? "—"}</h2>
            <div className="plug-head__controls">
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
              {selectedPlug && (
                <div className="power-toggle">
                  <span className="power-toggle__label">
                    {selectedPlug.state ? "Encès" : "Apagat"}
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={selectedPlug.state}
                    aria-label="Encendre o apagar el dispositiu"
                    className={selectedPlug.state ? "switch is-on" : "switch"}
                    disabled={setPlugState.isPending}
                    onClick={() =>
                      setPlugState.mutate({
                        id: selectedPlug.id,
                        on: !selectedPlug.state,
                      })
                    }
                  >
                    <span className="switch__knob" />
                  </button>
                </div>
              )}
            </div>
          </div>
          {selectedPlug && (
            <BoostControl plugId={selectedPlug.id} boost={boostFor(selectedPlug.id)} />
          )}
          {setPlugState.isError && (
            <p className="error-text">
              No s'ha pogut contactar amb el dispositiu.
            </p>
          )}
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

          <section className="card heatmap-card">
            <div className="card-head">
              <span className="card-eyebrow">Mapa de calor</span>
              <h2>Consum per hora i dia</h2>
            </div>
            {heatmap && heatmap.cells.length > 0 ? (
              <PlugHeatmap data={heatmap} />
            ) : (
              <div className="placeholder">
                Sense dades per al mapa de calor.
              </div>
            )}
          </section>

          <section className="card stats-card">
            <div className="card-head">
              <span className="card-eyebrow">Informació general</span>
              <h2>Estadístiques i previsió</h2>
            </div>
            {stats ? (
              <PlugStatsPanel data={stats} />
            ) : (
              <div className="placeholder">Carregant estadístiques…</div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
