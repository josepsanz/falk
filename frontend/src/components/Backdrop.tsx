import { useMemo } from "react";

interface Spark {
  top: number;
  left: number;
  size: number;
  delay: number;
  duration: number;
  peak: number;
}

type Dir = "ltr" | "rtl" | "ttb" | "btt";

interface Electron {
  dir: Dir;
  cross: number;
  progress: number;
  duration: number;
  len: number;
  opacity: number;
  teal: boolean;
}

const SPARK_COUNT = 34;
const ELECTRON_COUNT = 14;
const DIRS: Dir[] = ["ltr", "rtl", "ttb", "btt"];

function makeSparks(): Spark[] {
  return Array.from({ length: SPARK_COUNT }, () => ({
    top: Math.random() * 100,
    left: Math.random() * 100,
    size: 2.5 + Math.random() * 3.5,
    delay: Math.random() * 13,
    duration: 5.5 + Math.random() * 7.5,
    peak: 0.4 + Math.random() * 0.42,
  }));
}

function makeElectrons(): Electron[] {
  return Array.from({ length: ELECTRON_COUNT }, (_, i) => ({
    dir: DIRS[i % 4],
    cross: 4 + Math.random() * 92,
    progress: Math.random(),
    duration: 4 + Math.random() * 9,
    len: 12 + Math.random() * 28,
    opacity: 0.2 + Math.random() * 0.35,
    teal: Math.random() < 0.28,
  }));
}

export function Backdrop() {
  const sparks = useMemo(makeSparks, []);
  const electrons = useMemo(makeElectrons, []);

  return (
    <div className="backdrop" aria-hidden="true">
      {sparks.map((s, i) => (
        <span
          key={`s${i}`}
          className="spark"
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: `${s.size}px`,
            height: `${s.size}px`,
            animationDelay: `${s.delay}s`,
            animationDuration: `${s.duration}s`,
            "--peak": s.peak,
          } as React.CSSProperties}
        />
      ))}
      {electrons.map((e, i) => {
        const isH = e.dir === "ltr" || e.dir === "rtl";
        const color = e.teal
          ? "rgba(45,212,191,0.9)"
          : "rgba(0,230,118,0.9)";
        const glow = e.teal
          ? "rgba(45,212,191,0.3)"
          : "rgba(0,230,118,0.3)";
        const style: React.CSSProperties = {
          animationDelay: `${-(e.progress * e.duration).toFixed(2)}s`,
          animationDuration: `${e.duration.toFixed(2)}s`,
          "--e-opacity": e.opacity,
          "--e-color": color,
          "--e-glow": glow,
        } as React.CSSProperties;

        if (isH) {
          style.top = `${e.cross}%`;
          style.width = `${e.len}px`;
        } else {
          style.left = `${e.cross}%`;
          style.height = `${e.len}px`;
        }

        return (
          <span
            key={`e${i}`}
            className={`electron electron--${e.dir}`}
            style={style}
          />
        );
      })}
    </div>
  );
}
