import { useMemo } from "react";

interface Spark {
  top: number;
  left: number;
  size: number;
  delay: number;
  duration: number;
  peak: number;
}

const SPARK_COUNT = 34;

function makeSparks(): Spark[] {
  return Array.from({ length: SPARK_COUNT }, () => ({
    top: Math.random() * 100,
    left: Math.random() * 100,
    size: 2.5 + Math.random() * 3.5, // 2.5–6px
    delay: Math.random() * 13, // staggered start
    // Non-integer, spread durations keep the overall pattern aperiodic.
    duration: 5.5 + Math.random() * 7.5, // 5.5–13s
    peak: 0.4 + Math.random() * 0.42, // light, but a touch more present
  }));
}

export function Backdrop() {
  const sparks = useMemo(makeSparks, []);

  return (
    <div className="backdrop" aria-hidden="true">
      {sparks.map((spark, index) => (
        <span
          key={index}
          className="spark"
          style={{
            top: `${spark.top}%`,
            left: `${spark.left}%`,
            width: `${spark.size}px`,
            height: `${spark.size}px`,
            animationDelay: `${spark.delay}s`,
            animationDuration: `${spark.duration}s`,
            "--peak": spark.peak,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}
