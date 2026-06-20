import { useState } from "react";

import type { CostSeries } from "../api/types";
import { CostChart } from "../components/CostChart";
import { Segmented } from "../components/Controls";
import { useMeterCostSeries, useMeterDeviceSeries, useMeters } from "../hooks";

// The point of this view is spotting whether consumption fell on expensive or
// cheap hours, so everything stays at hourly resolution — the historical card
// just widens the window (with zoom) rather than aggregating per day.
const WINDOW_OPTIONS = [
  { value: "2", label: "2 dies" },
  { value: "7", label: "7 dies" },
  { value: "30", label: "30 dies" },
  { value: "custom", label: "Personalitzat" },
];

const BREAKDOWN_OPTIONS = [
  { value: "total", label: "Total" },
  { value: "device", label: "Per dispositiu" },
];

function localMidnightIso(offsetDays = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return `${ymd(date)}T00:00:00`;
}

function ymd(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Exclusive end: the midnight after the chosen "to" day, so the whole day counts.
function dayAfter(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return `${ymd(new Date(y, m - 1, d + 1))}T00:00:00`;
}

// Drop trailing hours with neither energy nor a published price so the chart
// only extends as far ahead as ESIOS data actually exists in the DB.
function trimTrailingEmpty(series: CostSeries): CostSeries {
  const pts = series.points;
  let end = pts.length;
  while (
    end > 0 &&
    pts[end - 1].price_kwh == null &&
    pts[end - 1].energy_kwh == null
  ) {
    end--;
  }
  return end === pts.length ? series : { ...series, points: pts.slice(0, end) };
}

function CostSummary({ series }: { series: CostSeries }) {
  return (
    <div className="stat-grid cost-summary">
      <div className="stat">
        <span className="stat__label">Energia</span>
        <span className="stat__value">
          {series.total_energy_kwh.toFixed(2)}
          <small>kWh</small>
        </span>
      </div>
      <div className="stat">
        <span className="stat__label">Cost</span>
        <span className="stat__value">
          {series.total_cost_eur.toFixed(2)}
          <small>€</small>
        </span>
      </div>
      <div className="stat">
        <span className="stat__label">Preu mitjà</span>
        <span className="stat__value">
          {series.avg_price_kwh.toFixed(4)}
          <small>€/kWh</small>
        </span>
      </div>
    </div>
  );
}

export function Cost() {
  const { data: meters } = useMeters();
  const meterId = meters?.[0]?.id;

  // Span up to 48h (today + tomorrow) so the price line extends ahead once ESIOS
  // publishes tomorrow's prices; trailing hours without data are trimmed below.
  const { data: today } = useMeterCostSeries(
    meterId,
    "hour",
    localMidnightIso(),
    localMidnightIso(2),
  );
  const todayTrimmed = today ? trimTrailingEmpty(today) : undefined;

  // Per-device breakdown for today, on the same hourly range so the buckets align
  // with the cost series; rendered as stacked bars when the toggle is on.
  const [breakdown, setBreakdown] = useState(false);
  const { data: todayDevices } = useMeterDeviceSeries(
    meterId,
    "hour",
    localMidnightIso(),
    localMidnightIso(2),
  );

  const [windowMode, setWindowMode] = useState("7");
  const [customFrom, setCustomFrom] = useState(() => localMidnightIso(-6).slice(0, 10));
  const [customTo, setCustomTo] = useState(() => localMidnightIso(0).slice(0, 10));
  const isCustom = windowMode === "custom";
  const invalidRange = isCustom && customFrom > customTo;

  let historyFrom: string;
  let historyTo: string;
  if (isCustom) {
    historyFrom = `${customFrom}T00:00:00`;
    historyTo = dayAfter(customTo);
  } else {
    const windowDays = Number(windowMode);
    historyFrom = localMidnightIso(-(windowDays - 1));
    historyTo = localMidnightIso(1);
  }
  const { data: history, error: historyError } = useMeterCostSeries(
    meterId,
    "hour",
    historyFrom,
    historyTo,
  );

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <h1>Cost</h1>
          <p className="muted">{meters?.[0]?.name ?? "—"}</p>
        </div>
      </header>

      <section className="card series-card">
        <div className="card-head card-head--row">
          <div>
            <span className="card-eyebrow">Avui</span>
            <h2>Consum i preu per hora</h2>
          </div>
          <Segmented
            label=""
            value={breakdown ? "device" : "total"}
            options={BREAKDOWN_OPTIONS}
            onChange={(value) => setBreakdown(value === "device")}
          />
        </div>
        {todayTrimmed ? (
          <>
            <CostSummary series={todayTrimmed} />
            <CostChart
              series={todayTrimmed}
              valueKey="energy_kwh"
              hourOnly
              colorByPrice
              breakdown={breakdown ? todayDevices : undefined}
            />
          </>
        ) : (
          <div className="placeholder">Carregant consum d'avui…</div>
        )}
      </section>

      <section className="card series-card">
        <div className="card-head card-head--row">
          <div>
            <span className="card-eyebrow">Històric</span>
            <h2>Consum per hora vs preu</h2>
          </div>
          <div className="cost-range">
            {isCustom && (
              <div className="date-range">
                <input
                  type="date"
                  className="date-input"
                  value={customFrom}
                  max={customTo}
                  onChange={(e) => setCustomFrom(e.target.value)}
                />
                <span className="date-range__sep">→</span>
                <input
                  type="date"
                  className="date-input"
                  value={customTo}
                  min={customFrom}
                  onChange={(e) => setCustomTo(e.target.value)}
                />
              </div>
            )}
            <Segmented
              label=""
              value={windowMode}
              options={WINDOW_OPTIONS}
              onChange={setWindowMode}
            />
          </div>
        </div>
        {invalidRange ? (
          <div className="placeholder">
            La data d'inici ha de ser anterior o igual a la final.
          </div>
        ) : historyError ? (
          <div className="placeholder">
            Rang massa gran a resolució horària (màx. ~80 dies). Tria un interval
            més curt.
          </div>
        ) : history ? (
          <>
            <CostSummary series={history} />
            <CostChart series={history} valueKey="energy_kwh" />
          </>
        ) : (
          <div className="placeholder">Carregant històric…</div>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <span className="card-eyebrow">Llegenda</span>
          <h2>Com es calculen els valors</h2>
        </div>
        <dl className="legend-defs">
          <dt>Energia (kWh)</dt>
          <dd>
            Consum de cada hora del comptador acumulat: lectura màxima menys la
            mínima dins de l'hora (MAX−MIN), dividit per 1000.
          </dd>
          <dt>Preu (€/kWh)</dt>
          <dd>
            Preu PVPC horari publicat per ESIOS (indicador 1001). És constant
            durant tota l'hora (p. ex. 08:00–08:59) i salta a la següent — per
            això la línia és esglaonada.
          </dd>
          <dt>Cost (€)</dt>
          <dd>
            Energia × preu, calculat hora a hora i sumat. Les hores futures amb
            preu publicat però sense consum encara no tenen cost.
          </dd>
          <dt>Preu mitjà (€/kWh)</dt>
          <dd>
            Cost total ÷ energia total de la finestra: el preu efectiu que has
            pagat per kWh (ponderat pel consum, no la mitjana simple de preus).
          </dd>
          <dt>Color de l'àrea</dt>
          <dd>
            Tinta sota la línia de preu segons el preu de cada hora dins del dia:
            verd = hora barata, groc = intermèdia, vermell = hora cara.
          </dd>
        </dl>
      </section>
    </div>
  );
}
