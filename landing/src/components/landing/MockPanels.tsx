import type { ReactNode } from "react";

/* ------------------------------------------------------------------ */
/* StatPill — small floating metric card                              */
/* ------------------------------------------------------------------ */

type StatPillProps = {
  label: string;
  value: string;
  icon?: ReactNode;
  className?: string;
};

export function StatPill({ label, value, icon, className = "" }: StatPillProps) {
  return (
    <div
      className={`flex items-center gap-3 rounded-2xl border border-default bg-card/85 backdrop-blur-xl px-4 py-3 shadow-[var(--shadow)] ${className}`}
    >
      {icon && (
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-soft text-secondary border border-accent-soft-border">
          {icon}
        </div>
      )}
      <div className="leading-tight">
        <p className="text-sm font-bold text-primary">{value}</p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">
          {label}
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* InsightChip — AI insight tag                                       */
/* ------------------------------------------------------------------ */

export function InsightChip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-soft-border bg-accent-soft px-3 py-1 text-[11px] font-semibold text-secondary">
      <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-r from-btn-primary-from to-btn-primary-to" />
      {children}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* TopicBar — topic coverage progress bar                             */
/* ------------------------------------------------------------------ */

export function TopicBar({ name, score }: { name: string; score: number }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[11px]">
        <span className="font-medium text-secondary">{name}</span>
        <span className="font-semibold text-primary">{score}/10</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-black/40 border border-default">
        <div
          className="h-full rounded-full bg-gradient-to-r from-btn-primary-from to-btn-primary-to"
          style={{ width: `${score * 10}%` }}
        />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TranscriptLine — a single interviewer / candidate exchange        */
/* ------------------------------------------------------------------ */

type TranscriptLineProps = {
  speaker: "Interviewer" | "Candidate";
  text: string;
};

export function TranscriptLine({ speaker, text }: TranscriptLineProps) {
  const isCandidate = speaker === "Candidate";
  return (
    <div className="flex gap-3">
      <div
        className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[10px] font-bold ${
          isCandidate
            ? "bg-info-soft text-info border border-info-border"
            : "bg-accent-soft text-secondary border border-accent-soft-border"
        }`}
      >
        {isCandidate ? "C" : "I"}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">
          {speaker}
        </p>
        <p className="text-xs leading-relaxed text-secondary">{text}</p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* GlassCard — standard glass surface used across the marketing page   */
/* ------------------------------------------------------------------ */

export function GlassCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-3xl border border-default bg-card/85 backdrop-blur-xl shadow-[var(--shadow)] ${className}`}
    >
      {children}
    </div>
  );
}
