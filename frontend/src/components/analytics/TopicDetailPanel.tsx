"use client";

import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  AlertCircle,
  Clock,
  FileText,
  HelpCircle,
  BarChart2,
  CheckCircle2,
} from "lucide-react";
import type { TopicStat } from "@/types/dashboard";
import { GlassCard } from "@/components/landing/MockPanels";
import { timeAgo } from "@/utils/time";

interface TopicDetailPanelProps {
  stat: TopicStat | null;
}

export function TopicDetailPanel({ stat }: TopicDetailPanelProps) {
  if (!stat) {
    return (
      <GlassCard className="p-8 text-center flex flex-col items-center justify-center h-full min-h-[360px] text-muted border-dashed border-default">
        <div className="h-12 w-12 rounded-2xl bg-accent-soft flex items-center justify-center text-secondary mb-3 border border-accent-soft-border">
          <BarChart2 className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-primary mb-1">
          Select a Topic
        </h3>
        <p className="text-xs text-secondary/70 max-w-xs">
          Click any topic from the list to view in-depth performance metrics, key feedback insights, and question highlights.
        </p>
      </GlassCard>
    );
  }

  const avgScore = parseFloat(stat.average_score || "0");
  const highestScore = stat.highest_score ? parseFloat(stat.highest_score).toFixed(1) : "—";
  const lowestScore = stat.lowest_score ? parseFloat(stat.lowest_score).toFixed(1) : "—";

  const getScoreBadgeClass = (score: number) => {
    if (score >= 7.5) {
      return "bg-success-soft text-success border-success-border";
    }
    if (score >= 5.0) {
      return "bg-warning-soft text-warning border-warning-border";
    }
    return "bg-danger-soft text-danger border-danger-border";
  };

  const highestQ = stat.highest_scored_question;
  const lowestQ = stat.lowest_scored_question;

  return (
    <div className="overflow-hidden flex flex-col h-full min-w-0 rounded-3xl border border-default bg-card/85 backdrop-blur-xl transition-all duration-200">
      {/* Panel Header - shrink-0 */}
      <div className="bg-accent-soft/80 border-b border-default px-5 py-3.5 shrink-0 min-w-0 overflow-hidden">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 min-w-0">
              <span className="text-[10px] uppercase font-bold tracking-wider text-muted shrink-0">
                Topic Detail
              </span>
              <span className="text-muted/40 shrink-0">•</span>
              <span className="inline-flex items-center gap-1 text-[11px] text-secondary/70 truncate min-w-0">
                <Clock className="h-3 w-3 text-muted shrink-0" />
                {timeAgo(stat.last_assessed_at)}
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-primary truncate" title={stat.topic}>
              {stat.topic}
            </h3>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-secondary/70">
              <span className="inline-flex items-center gap-1 text-[11px]">
                <FileText className="h-3 w-3 text-muted" />
                {stat.interview_count} {stat.interview_count === 1 ? "interview assessed" : "interviews assessed"}
              </span>
            </div>
          </div>

          {/* Average Score Box */}
          <div className="flex flex-col items-end shrink-0">
            <div
              className={`flex items-baseline gap-1 px-2.5 py-1 rounded-xl border font-bold text-base leading-none ${getScoreBadgeClass(
                avgScore
              )}`}
            >
              <span>{avgScore.toFixed(1)}</span>
              <span className="text-[10px] font-medium opacity-70">/ 10</span>
            </div>
            <span className="text-[9px] font-semibold text-muted uppercase mt-0.5">
              Avg Score
            </span>
          </div>
        </div>

        {/* Score Spread Quick Metrics */}
        <div className="mt-3 grid grid-cols-2 gap-2 pt-2.5 border-t border-accent/40">
          <div className="rounded-xl border border-default bg-surface/50 px-3 py-1.5">
            <span className="block text-[9px] uppercase font-bold text-muted">
              Highest Score
            </span>
            <span className="text-xs sm:text-sm font-bold text-primary">
              {highestScore}
            </span>
          </div>
          <div className="rounded-xl border border-default bg-surface/50 px-3 py-1.5">
            <span className="block text-[9px] uppercase font-bold text-muted">
              Lowest Score
            </span>
            <span className="text-xs sm:text-sm font-bold text-primary">
              {lowestScore}
            </span>
          </div>
        </div>
      </div>

      {/* Panel Body - flex-1 min-h-0 with internal scroll */}
      <div className="p-4 sm:p-5 space-y-3.5 flex-1 min-h-0 overflow-y-auto">
        {/* Key Feedback Insight */}
        {stat.best_feedback ? (
          <div className="rounded-2xl border border-default bg-surface/40 p-3.5 relative overflow-hidden">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-primary mb-1.5">
              <div className="flex h-5 w-5 items-center justify-center rounded-md bg-accent-soft text-secondary border border-accent-soft-border">
                <Sparkles className="h-3 w-3" />
              </div>
              <span>Key Feedback Insight</span>
            </div>
            <p className="text-xs text-secondary leading-relaxed pl-1 italic">
              &ldquo;{stat.best_feedback}&rdquo;
            </p>
          </div>
        ) : (
          <div className="rounded-2xl border border-default bg-surface/30 p-3 text-xs text-muted">
            No specific feedback highlights recorded for this topic yet.
          </div>
        )}

        {/* Top Scored Question */}
        {highestQ && (
          <div className="rounded-2xl border border-default bg-surface/40 p-3.5 space-y-2 transition-colors hover:border-accent-soft-border">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-success">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                <span>Top Scored Question</span>
              </div>
              {highestQ.average_score && (
                <span className="inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[10px] font-bold border bg-success-soft text-success border-success-border">
                  {parseFloat(highestQ.average_score).toFixed(1)} / 10
                </span>
              )}
            </div>

            {highestQ.question && (
              <p className="text-xs text-primary font-medium leading-snug">
                {highestQ.question}
              </p>
            )}

            {highestQ.feedback && (
              <p className="text-[11px] text-secondary/70 leading-relaxed border-l-2 border-accent-soft-border pl-2 mt-1">
                {highestQ.feedback}
              </p>
            )}
          </div>
        )}

        {/* Lowest Scored Question (if available and different) */}
        {lowestQ && lowestQ.question !== highestQ?.question && (
          <div className="rounded-2xl border border-default bg-surface/40 p-3.5 space-y-2 transition-colors hover:border-warning-border/50">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-warning">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span>Needs Focus Question</span>
              </div>
              {lowestQ.average_score && (
                <span className="inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[10px] font-bold border bg-warning-soft text-warning border-warning-border">
                  {parseFloat(lowestQ.average_score).toFixed(1)} / 10
                </span>
              )}
            </div>

            {lowestQ.question && (
              <p className="text-xs text-primary font-medium leading-snug">
                {lowestQ.question}
              </p>
            )}

            {lowestQ.feedback && (
              <p className="text-[11px] text-secondary/70 leading-relaxed border-l-2 border-warning-border/40 pl-2 mt-1">
                {lowestQ.feedback}
              </p>
            )}
          </div>
        )}

        {/* Action Link: Drill into all questions */}
        <div className="pt-1">
          <Link
            href={`/analytics/topics/${encodeURIComponent(stat.topic)}`}
            className="w-full inline-flex items-center justify-between rounded-xl bg-surface-hover border border-default px-3.5 py-2.5 text-xs font-semibold text-primary transition-all duration-200 hover:border-accent-soft-border hover:bg-accent-soft hover:shadow-[0_0_15px_-4px_var(--shadow-glow)] group"
          >
            <span className="inline-flex items-center gap-2">
              <HelpCircle className="h-3.5 w-3.5 text-secondary" />
              <span>Drill into all questions for {stat.topic}</span>
            </span>
            <ArrowRight className="h-3.5 w-3.5 text-secondary transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </div>
  );
}
