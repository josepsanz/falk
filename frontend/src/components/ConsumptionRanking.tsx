import type { Ranking } from "../api/types";

function formatValue(value: number, unit: string): string {
  return unit === "W" ? `${Math.round(value)}` : value.toFixed(2);
}

export function ConsumptionRanking({ data }: { data: Ranking }) {
  const devices = [...data.devices].sort((a, b) => b.value - a.value);
  const total = data.total || 1;
  const max = Math.max(...devices.map((d) => d.value), data.unassigned, 1);

  return (
    <div className="ranking">
      {devices.map((device, index) => (
        <div className="ranking__row" key={device.id}>
          <span className="ranking__rank">{index + 1}</span>
          <span className="ranking__name">{device.name}</span>
          <span className="ranking__bar">
            <span
              className="ranking__fill"
              style={{ width: `${(device.value / max) * 100}%` }}
            />
          </span>
          <span className="ranking__val">
            {formatValue(device.value, data.unit)} {data.unit}
          </span>
          <span className="ranking__pct">
            {((device.value / total) * 100).toFixed(0)}%
          </span>
        </div>
      ))}
      <div className="ranking__row ranking__row--muted">
        <span className="ranking__rank">·</span>
        <span className="ranking__name">Sense assignar</span>
        <span className="ranking__bar">
          <span
            className="ranking__fill ranking__fill--muted"
            style={{ width: `${(data.unassigned / max) * 100}%` }}
          />
        </span>
        <span className="ranking__val">
          {formatValue(data.unassigned, data.unit)} {data.unit}
        </span>
        <span className="ranking__pct">
          {((data.unassigned / total) * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
