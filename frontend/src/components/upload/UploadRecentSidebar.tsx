"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  Clock,
  ArrowRight,
  ChevronRight,
  FolderClosed,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { getInterviews } from "@/services/interviewApi";
import { getDashboardOverview } from "@/services/dashboardApi";
import type { InterviewListItem } from "@/types/interview";
import type { DashboardOverview } from "@/types/dashboard";
import { timeAgo } from "@/utils/time";

export default function UploadRecentSidebar() {
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadRecent() {
      try {
        setLoading(true);
        const [interviewsRes, overviewRes] = await Promise.allSettled([
          getInterviews(),
          getDashboardOverview(),
        ]);

        if (isMounted) {
          if (interviewsRes.status === "fulfilled") {
            const valid = interviewsRes.value.items.filter(
              (i) => i.status !== "FAILED" && i.status !== "CANCELLED"
            );
            setInterviews(valid.slice(0, 5));
            setTotalCount(interviewsRes.value.meta.total);
          }
          if (overviewRes.status === "fulfilled") {
            setOverview(overviewRes.value);
          }
        }
      } catch (err) {
        console.error("Failed to load recent sidebar data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadRecent();
    return () => {
      isMounted = false;
    };
  }, []);

  const strongestTopic = overview?.strongest_topic ?? null;
  const bestInterview = overview?.best_interview ?? null;

  return (
    <aside className="flex flex-col gap-5 w-full">
      {/* 1. Quick Stats Card */}
      <div className="rounded-3xl border border-default bg-card/85 p-5 shadow-[var(--shadow)] backdrop-blur-xl space-y-4">
        <div className="flex items-center justify-between border-b border-default pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-soft text-secondary border border-accent-soft-border">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted">
              Quick Intelligence
            </h2>
          </div>
          <Link
            href="/analytics"
            className="text-[11px] font-semibold text-secondary hover:text-primary transition-colors inline-flex items-center gap-1"
          >
            Analytics <ChevronRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Mini metric pills */}
        <div className="grid grid-cols-2 gap-2.5">
          <div className="rounded-2xl border border-default bg-surface/50 p-3">
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted">
              Total Candidates
            </span>
            <span className="text-lg font-bold text-primary mt-0.5 block">
              {loading ? "…" : (totalCount ?? interviews.length)}
            </span>
          </div>

          <div className="rounded-2xl border border-default bg-surface/50 p-3">
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted">
              Top Score
            </span>
            <span className="text-lg font-bold text-primary mt-0.5 block">
              {loading
                ? "…"
                : bestInterview?.overall_score
                ? `${parseFloat(bestInterview.overall_score).toFixed(1)}/10`
                : "—"}
            </span>
          </div>
        </div>

        {/* Strongest concept highlight */}
        {strongestTopic && (
          <div className="rounded-2xl border border-success-border/40 bg-success-soft/50 p-3 flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1">
              <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-success">
                <TrendingUp className="h-3 w-3" />
                <span>Top Strength</span>
              </span>
              <p className="text-xs font-bold text-primary truncate mt-0.5" title={strongestTopic.topic}>
                {strongestTopic.topic}
              </p>
            </div>
            {strongestTopic.average_score && (
              <span className="px-2 py-0.5 rounded-lg text-xs font-bold border border-success-border bg-success-soft text-success shrink-0">
                {parseFloat(strongestTopic.average_score).toFixed(1)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* 2. Recent Uploads Card */}
      <div className="rounded-3xl border border-default bg-card/85 p-5 shadow-[var(--shadow)] backdrop-blur-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-default pb-3 mb-3">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-soft text-secondary border border-accent-soft-border">
                <FolderClosed className="h-3.5 w-3.5" />
              </div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted">
                Recent Evaluations
              </h2>
            </div>
            <span className="text-[11px] font-medium text-muted">
              {interviews.length} recent
            </span>
          </div>

          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 rounded-2xl bg-surface-hover/60 border border-default" />
              ))}
            </div>
          ) : interviews.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted space-y-1">
              <p className="font-semibold text-secondary">No interviews yet</p>
              <p className="text-[11px]">Upload a candidate video above to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {interviews.map((item) => {
                const displayName = item.title || `Interview #${item.id.slice(0, 8)}`;
                const isReady = item.status === "COMPLETED";
                const score = item.overall_score ? parseFloat(item.overall_score).toFixed(1) : null;

                return (
                  <Link
                    key={item.id}
                    href={`/interviews/${item.id}`}
                    className="flex items-center justify-between gap-3 p-2.5 rounded-2xl border border-default bg-surface/40 hover:bg-surface-hover hover:border-accent-soft-border transition-all duration-150 group"
                  >
                    <div className="min-w-0 flex-1 pl-1">
                      <p className="text-xs font-semibold text-primary truncate group-hover:text-secondary transition-colors" title={displayName}>
                        {displayName}
                      </p>
                      <div className="mt-0.5 flex items-center gap-2 text-[10px] text-secondary/60">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-2.5 w-2.5 text-muted" />
                          {timeAgo(item.created_at)}
                        </span>
                        {item.hiring_decision && (
                          <>
                            <span>•</span>
                            <span className="font-medium">
                              {item.hiring_decision.replace("_", " ")}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {isReady && score ? (
                        <span className="px-2 py-0.5 rounded-lg text-xs font-bold border border-accent-soft-border bg-accent-soft text-primary">
                          {score}
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium border border-info-border bg-info-soft text-info animate-pulse">
                          {item.status}
                        </span>
                      )}
                      <ChevronRight className="h-3.5 w-3.5 text-muted group-hover:text-primary transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        <div className="pt-4 mt-3 border-t border-default">
          <Link
            href="/interviews"
            className="w-full inline-flex items-center justify-between rounded-xl bg-surface-hover border border-default px-3.5 py-2 text-xs font-semibold text-secondary hover:text-primary hover:border-accent-soft-border transition-all duration-150 group"
          >
            <span>View All in Repository</span>
            <ArrowRight className="h-3.5 w-3.5 text-muted group-hover:text-primary transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </div>
    </aside>
  );
}
