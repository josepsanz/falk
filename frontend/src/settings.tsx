import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

// Client-side preferences, persisted to localStorage. New tunable parameters
// should be added here (with a default) and surfaced on the Settings page.
export interface Settings {
  gaugeTotalMax: number;
  gaugePhaseMax: number;
}

export const SETTINGS_DEFAULTS: Settings = {
  gaugeTotalMax: 7400,
  gaugePhaseMax: 3500,
};

const STORAGE_KEY = "falk.settings";

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw
      ? { ...SETTINGS_DEFAULTS, ...(JSON.parse(raw) as Partial<Settings>) }
      : SETTINGS_DEFAULTS;
  } catch {
    return SETTINGS_DEFAULTS;
  }
}

interface SettingsContextValue {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  reset: () => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(loadSettings);

  const update = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const reset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setSettings(SETTINGS_DEFAULTS);
  }, []);

  return (
    <SettingsContext.Provider value={{ settings, update, reset }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return ctx;
}
