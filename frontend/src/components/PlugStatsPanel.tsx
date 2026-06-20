import type { PlugStats } from "../api/types";

function Stat({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit?: string;
}) {
  return (
    <div className="stat">
      <span className="stat__label">{label}</span>
      <span className="stat__value">
        {value}
        {unit && <small>{unit}</small>}
      </span>
    </div>
  );
}

export function PlugStatsPanel({ data }: { data: PlugStats }) {
  const trend = data.trend_pct;
  const trendClass =
    trend == null ? "" : trend > 0 ? "is-up" : trend < 0 ? "is-down" : "";

  return (
    <div className="stats">
      <div className="stats__group">
        <h3>Potència</h3>
        <div className="stat-grid">
          <Stat label="Mitjana" value={`${Math.round(data.power_avg)}`} unit="W" />
          <Stat
            label="Mediana"
            value={`${Math.round(data.power_median)}`}
            unit="W"
          />
          <Stat label="P95" value={`${Math.round(data.power_p95)}`} unit="W" />
          <Stat label="Màxim" value={`${Math.round(data.power_max)}`} unit="W" />
          <Stat
            label="% actiu"
            value={`${Math.round(data.active_ratio * 100)}`}
            unit="%"
          />
        </div>
      </div>

      <div className="stats__group">
        <h3>Energia</h3>
        <div className="stat-grid">
          <Stat label="Avui" value={data.energy_today_kwh.toFixed(2)} unit="kWh" />
          <Stat
            label="Últims 7 dies"
            value={data.energy_last7_kwh.toFixed(2)}
            unit="kWh"
          />
          <Stat
            label="Mitjana diària"
            value={data.energy_daily_avg_kwh.toFixed(2)}
            unit="kWh"
          />
          <Stat
            label={`Total (${data.window_days}d)`}
            value={data.energy_total_kwh.toFixed(1)}
            unit="kWh"
          />
        </div>
      </div>

      <div className="stats__group">
        <h3>Cost</h3>
        <div className="stat-grid">
          <Stat label="Avui" value={data.cost_today_eur.toFixed(2)} unit="€" />
          <Stat
            label="Últims 7 dies"
            value={data.cost_last7_eur.toFixed(2)}
            unit="€"
          />
          <Stat
            label={`Total (${data.window_days}d)`}
            value={data.cost_total_eur.toFixed(2)}
            unit="€"
          />
        </div>
      </div>

      <div className="stats__group">
        <h3>Previsió</h3>
        <div className="stat-grid">
          <Stat
            label="Pròxim dia"
            value={data.forecast_next_day_kwh.toFixed(2)}
            unit="kWh"
          />
          <Stat
            label="Pròxims 30 dies"
            value={data.forecast_next_30d_kwh.toFixed(1)}
            unit="kWh"
          />
          <div className="stat">
            <span className="stat__label">Tendència (7d)</span>
            <span className={`stat__value ${trendClass}`}>
              {trend == null
                ? "—"
                : `${trend > 0 ? "▲" : trend < 0 ? "▼" : ""} ${Math.abs(trend).toFixed(0)}%`}
            </span>
          </div>
        </div>
      </div>

      <p className="stats__note">
        Energia estimada (potència × interval de mostreig); cost = energia
        estimada × preu PVPC horari. Previsió = mitjana diària dels últims 7
        dies; tendència = últims 7 dies vs els 7 anteriors.
      </p>
    </div>
  );
}
