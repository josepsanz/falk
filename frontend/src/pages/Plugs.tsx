import { useEffect, useState } from "react";

import type { Granularity, Metric, Plug } from "../api/types";
import { BoostControl } from "../components/BoostControl";
import { CostChart } from "../components/CostChart";
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
  usePlugCostSeries,
  usePlugHeatmap,
  usePlugLatest,
  usePlugSeries,
  usePlugStats,
  usePlugs,
  useSetPlugState,
} from "../hooks";
import { ACCENTS } from "../theme";

// Period for the headline power/energy/cost summary (days back from now).
const SUMMARY_WINDOW_OPTIONS = [
  { value: "1", label: "Avui" },
  { value: "7", label: "7 dies" },
  { value: "30", label: "30 dies" },
];

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
  // The energy view shows consumption (kWh) bars alongside the hourly price
  // (with cost in the tooltip), so it pulls the cost series rather than the
  // plain energy series; only the power view uses the power series.
  const showCost = metric === "energy";
  const { data: series } = usePlugSeries(showCost ? undefined : selected, {
    metric,
    granularity,
  });
  const { data: costSeries } = usePlugCostSeries(
    showCost ? selected : undefined,
    granularity,
  );
  const { data: heatmap } = usePlugHeatmap(selected);
  const { data: stats } = usePlugStats(selected);

  const [summaryWindow, setSummaryWindow] = useState("7");

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
          <h1>Dispositius</h1>
          <p className="muted">Consum per aparell</p>
        </div>
      </header>

      <section className="card">
        <div className="card-head card-head--row">
          <div>
            <span className="card-eyebrow">Resum per dispositiu</span>
            <h2>Potència, energia i cost</h2>
          </div>
          <Segmented
            label=""
            value={summaryWindow}
            options={SUMMARY_WINDOW_OPTIONS}
            onChange={setSummaryWindow}
          />
        </div>
        <div className="device-kpi-grid">
          {(plugs ?? []).map((plug) => (
            <DeviceKpiCard
              key={plug.id}
              plug={plug}
              windowDays={Number(summaryWindow)}
              active={plug.id === selected}
              boosted={Boolean(boostFor(plug.id))}
              onSelect={() => setSelected(plug.id)}
            />
          ))}
        </div>
      </section>

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
          {showCost ? (
            costSeries ? (
              <CostChart
                series={costSeries}
                valueKey="energy_kwh"
                secondaryValueKey="cost_eur"
                colorByPrice
                hourOnly={granularity === "hour"}
              />
            ) : (
              <div className="placeholder">Carregant cost…</div>
            )
          ) : series ? (
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
  );
}

function DeviceKpiCard({
  plug,
  windowDays,
  active,
  boosted,
  onSelect,
}: {
  plug: Plug;
  windowDays: number;
  active: boolean;
  boosted: boolean;
  onSelect: () => void;
}) {
  const { data } = usePlugStats(plug.id, windowDays);
  const metric = (value: string, unit: string) => (
    <span className="device-kpi__value">
      {data ? value : "—"}
      <small>{unit}</small>
    </span>
  );

  return (
    <button
      type="button"
      className={active ? "device-kpi is-active" : "device-kpi"}
      onClick={onSelect}
    >
      <div className="device-kpi__head">
        <span className="device-kpi__name">{plug.name}</span>
        {boosted && (
          <span className="boost-tag" title="Boost actiu">
            ⚡
          </span>
        )}
        <span className={plug.state ? "dot dot--on" : "dot"} />
      </div>
      <div className="device-kpi__metrics">
        <div className="device-kpi__metric">
          <span className="device-kpi__label">Potència</span>
          {metric(data ? `${Math.round(data.power_avg)}` : "", "W")}
        </div>
        <div className="device-kpi__metric">
          <span className="device-kpi__label">Energia</span>
          {metric(data ? data.energy_total_kwh.toFixed(2) : "", "kWh")}
        </div>
        <div className="device-kpi__metric">
          <span className="device-kpi__label">Cost</span>
          {metric(data ? data.cost_total_eur.toFixed(2) : "", "€")}
        </div>
      </div>
    </button>
  );
}
