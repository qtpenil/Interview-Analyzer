"use client";

type ScoreRingProps = {
  value: number; // 0 - 10
  size?: number;
  stroke?: number;
  label?: string;
  strokeColor?: string; // CSS color for the arc, defaults to gradient
  trackColor?: string; // CSS color for the background track, defaults to var(--accent-soft)
  trackOpacity?: number; // 0-1 opacity for the background track
  valueClassName?: string; // CSS classes for the score number, defaults to text-primary
};

export function ScoreRing({
  value,
  size = 96,
  stroke = 8,
  label,
  strokeColor,
  trackColor,
  trackOpacity,
  valueClassName,
}: ScoreRingProps) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 10) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor || "var(--accent-soft)"}
          strokeOpacity={trackOpacity}
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor || "url(#scoreGradient)"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--gradient-start)" />
            <stop offset="100%" stopColor="var(--gradient-end)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-xl font-bold leading-none ${valueClassName || "text-primary"}`}>
          {value.toFixed(2)}
        </span>
        {label && (
          <span className="text-[9px] font-semibold uppercase tracking-wider text-muted mt-1">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}