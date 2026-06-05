import type { Settings } from "../settings";
import { useSettings } from "../settings";

interface NumberFieldProps {
  label: string;
  hint: string;
  unit: string;
  value: number;
  min?: number;
  step?: number;
  onChange: (value: number) => void;
}

function NumberField({
  label,
  hint,
  unit,
  value,
  min = 0,
  step = 100,
  onChange,
}: NumberFieldProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <span className="field__hint">{hint}</span>
      <div className="field__input">
        <input
          type="number"
          value={value}
          min={min}
          step={step}
          onChange={(event) => {
            const next = Number(event.target.value);
            if (!Number.isNaN(next)) {
              onChange(next);
            }
          }}
        />
        <span className="field__unit">{unit}</span>
      </div>
    </label>
  );
}

export function Settings() {
  const { settings, update, reset } = useSettings();

  const setField = (key: keyof Settings) => (value: number) =>
    update({ [key]: value });

  return (
    <div className="page">
      <header className="page__head">
        <div>
          <h1>Configuració</h1>
          <p className="muted">Els canvis es desen automàticament en aquest navegador</p>
        </div>
        <button type="button" className="btn-ghost" onClick={reset}>
          Restaura valors per defecte
        </button>
      </header>

      <section className="card settings-section">
        <h2>Escales dels indicadors</h2>
        <p className="muted">
          Valor màxim (fons d'escala) de cada gauge del panell. Ajusta'l a la teva
          potència contractada.
        </p>
        <div className="fields">
          <NumberField
            label="Consum total"
            hint="Fons d'escala del gauge principal"
            unit="W"
            value={settings.gaugeTotalMax}
            step={100}
            onChange={setField("gaugeTotalMax")}
          />
          <NumberField
            label="Per fase (L1/L2/L3)"
            hint="Fons d'escala dels gauges de fase"
            unit="W"
            value={settings.gaugePhaseMax}
            step={100}
            onChange={setField("gaugePhaseMax")}
          />
        </div>
      </section>
    </div>
  );
}
