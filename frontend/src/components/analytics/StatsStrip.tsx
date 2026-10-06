"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Trophy, ExternalLink } from "lucide-react";
import type { StrongestWeakestTopic, BestInterview } from "@/types/dashboard";

interface StatsStripProps {
  strongestTopic: StrongestWeakestTopic | null;
  weakestTopic: StrongestWeakestTopic | null;
  bestInterview: BestInterview | null;
  selectedTopic: string | null;
  onSelectTopic: (topic: string) => void;
}

export function StatsStrip({
  strongestTopic,
  weakestTopic,
  bestInterview,
  selectedTopic,
  onSelectTopic,
}: StatsStripProps) {
  const formatScore = (val: string | null) => {
    if (!val) return "—";
    const num = parseFloat(val);
    return isNaN(num) ? val : num.toFixed(1);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 sm:gap-3 shrink-0 items-stretch">
      {/* 1. Strongest Topic Chip */}
      {strongestTopic ? (
        <button
          type="button"
          onClick={() => onSelectTopic(strongestTopic.topic)}
          aria-current={selectedTopic === strongestTopic.topic || undefined}
          className="flex h-full items-center justify-between gap-3 px-3.5 py-2 rounded-2xl border border-default bg-card/85 hover:bg-surface-hover hover:border-accent-soft-border transition-all duration-150 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-secondary">
              <TrendingUp className="h-3 w-3 shrink-0" />
              <span>Strongest Topic</span>
            </div>
            <p className="text-xs sm:text-sm font-bold text-primary truncate mt-0.5" title={strongestTopic.topic}>
              {strongestTopic.topic}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-lg text-xs font-bold border border-accent bg-accent text-white">
              {formatScore(strongestTopic.average_score)}
            </span>
          </div>
        </button>
      ) : (
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-2xl border border-default bg-card/50 text-xs text-muted">
          <span>No strongest topic recorded</span>
        </div>
      )}

      {/* 2. Needs Focus Chip */}
      {weakestTopic ? (
        <button
          type="button"
          onClick={() => onSelectTopic(weakestTopic.topic)}
          aria-current={selectedTopic === weakestTopic.topic || undefined}
          className="flex h-full items-center justify-between gap-3 px-3.5 py-2 rounded-2xl border border-default bg-card/85 hover:bg-surface-hover hover:border-accent-soft-border transition-all duration-150 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-secondary">
              <TrendingDown className="h-3 w-3 shrink-0" />
              <span>Needs Focus</span>
            </div>
            <p className="text-xs sm:text-sm font-bold text-primary truncate mt-0.5" title={weakestTopic.topic}>
              {weakestTopic.topic}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-lg text-xs font-bold border border-accent bg-accent text-white">
              {formatScore(weakestTopic.average_score)}
            </span>
          </div>
        </button>
      ) : (
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-2xl border border-default bg-card/50 text-xs text-muted">
          <span>No focus area identified</span>
        </div>
      )}

      {/* 3. Best Interview Chip */}
      {bestInterview && bestInterview.interview_id ? (
        <Link
          href={`/interviews/${bestInterview.interview_id}`}
          className="flex h-full items-center justify-between gap-3 px-3.5 py-2 rounded-2xl border border-default bg-card/85 hover:bg-surface-hover hover:border-accent-soft-border transition-all duration-150 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-secondary">
              <Trophy className="h-3 w-3 shrink-0 text-amber-400" />
              <span>Best Interview</span>
            </div>
            <p className="text-xs sm:text-sm font-bold text-primary truncate mt-0.5" title={bestInterview.title || "Untitled Interview"}>
              {bestInterview.title || "Untitled Interview"}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-lg text-xs font-bold border border-accent-soft-border bg-accent-soft text-primary">
              {formatScore(bestInterview.overall_score)}
            </span>
            <ExternalLink className="h-3 w-3 text-muted group-hover:text-primary transition-colors" />
          </div>
        </Link>
      ) : (
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-2xl border border-default bg-card/50 text-xs text-muted">
          <span>No interview evaluations yet</span>
        </div>
      )}
    </div>
  );
}
