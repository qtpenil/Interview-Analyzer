"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Layers,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { getDashboardOverview } from "@/services/dashboardApi";
import type { DashboardOverview } from "@/types/dashboard";
import { extractApiError } from "@/services/apiClient";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { GlassCard } from "@/components/landing/MockPanels";
import { StatsStrip } from "@/components/analytics/StatsStrip";
import { TopicRowList } from "@/components/analytics/TopicRowList";
import { TopicDetailPanel } from "@/components/analytics/TopicDetailPanel";

export default function AnalyticsOverviewPage() {
  const authStatus = useRequireAuth();
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  useEffect(() => {
    if (authStatus !== "authed") return;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const overview = await getDashboardOverview();
        setData(overview);
      } catch (err) {
        console.error("Failed to load dashboard overview:", err);
        setError(extractApiError(err));
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [authStatus]);

  // Default selection to strongest topic or first topic when data arrives
  useEffect(() => {
    if (data?.topics && data.topics.length > 0) {
      if (!selectedTopic || !data.topics.some((t) => t.topic === selectedTopic)) {
        const defaultTopic =
          data.strongest_topic?.topic &&
          data.topics.some((t) => t.topic === data.strongest_topic?.topic)
            ? data.strongest_topic.topic
            : data.topics[0].topic;
        setSelectedTopic(defaultTopic);
      }
    }
  }, [data, selectedTopic]);

  if (authStatus === "checking") {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-secondary/50">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-soft-border border-t-secondary" />
          <span className="text-sm">Verifying your session…</span>
        </div>
      </main>
    );
  }

  if (authStatus === "unauthed") {
    return null;
  }

  const topics = data?.topics || [];
  const hasTopics = topics.length > 0;

  const selectedTopicStat =
    topics.find((t) => t.topic === selectedTopic) || null;

  return (
    <main className="py-3 sm:py-4 px-3 sm:px-4 w-full max-w-8xl mx-auto flex flex-col overflow-x-clip lg:h-screen lg:max-h-screen lg:overflow-hidden">
      {/* 1. Header (Compact & Fixed) */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-default pb-3 mb-3 shrink-0">
        <div>
          <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted mb-0.5">
            <Sparkles className="h-3.5 w-3.5 text-secondary" />
            <span>Cross-Interview Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">
            Interview Analytics
          </h1>
          <p className="text-xs sm:text-sm text-secondary/70">
            Aggregated concept mastery, question performance, and trends across all candidate evaluations.
          </p>
        </div>

        {hasTopics && (
          <div className="flex items-center gap-2 shrink-0">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-card/90 px-3 py-1 text-xs font-semibold text-secondary shadow-sm border border-default">
              <Layers className="h-3 w-3 text-secondary/70" />
              {topics.length} {topics.length === 1 ? "Topic" : "Topics"}
            </span>
          </div>
        )}
      </header>

      {/* Error Alert */}
      {error && (
        <div className="rounded-2xl border border-danger/20 bg-danger-soft p-3 text-xs text-danger flex items-center gap-2.5 shrink-0 mb-3">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-4 animate-pulse flex-1 flex flex-col min-h-0">
          {/* Stats strip skeleton */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 shrink-0">
            <div className="h-16 rounded-2xl bg-surface-hover/60 border border-default" />
            <div className="h-16 rounded-2xl bg-surface-hover/60 border border-default" />
            <div className="h-16 rounded-2xl bg-surface-hover/60 border border-default" />
          </div>
          {/* Master-Detail skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-0">
            <div className="lg:col-span-7 h-[480px] lg:h-full rounded-3xl bg-surface-hover/60 border border-default" />
            <div className="lg:col-span-5 h-[480px] lg:h-full rounded-3xl bg-surface-hover/60 border border-default" />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && !hasTopics && (
        <div className="flex-1 flex items-center justify-center">
          <GlassCard className="p-10 text-center max-w-lg mx-auto">
            <div className="flex h-14 w-14 mx-auto items-center justify-center rounded-2xl bg-accent-soft text-secondary border border-accent-soft-border mb-3">
              <Layers className="h-7 w-7" />
            </div>
            <h2 className="text-lg font-bold text-primary mb-1.5">
              No Analytics Available Yet
            </h2>
            <p className="text-xs sm:text-sm text-secondary/70 mb-5">
              Once you upload and process candidate interviews, aggregated performance statistics and topic mastery insights will appear here.
            </p>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-2 text-xs font-semibold text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>Upload New Interview</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </GlassCard>
        </div>
      )}

      {/* Dashboard Content */}
      {!loading && hasTopics && data && (
        <div className="flex-1 flex flex-col min-h-0 space-y-3">
          {/* 2. Compact Stats Strip (Strongest / Needs Focus / Best Interview) */}
          {(data.strongest_topic || data.weakest_topic || data.best_interview) && (
            <StatsStrip
              strongestTopic={data.strongest_topic}
              weakestTopic={data.weakest_topic}
              bestInterview={data.best_interview}
              selectedTopic={selectedTopic}
              onSelectTopic={setSelectedTopic}
            />
          )}

          {/* 3. Master-Detail Layout (Fixed height, only internal panes scroll) */}
          <section
            aria-label="Topic Breakdown"
            className="flex-1 min-h-0 flex flex-col overflow-hidden pb-1"
          >
            <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch overflow-hidden">
              {/* Left side: Search & Dense Topic Rows */}
              <div className="lg:col-span-7 h-[420px] lg:h-full flex flex-col min-h-0 min-w-0">
                <TopicRowList
                  topics={topics}
                  selectedTopic={selectedTopic}
                  onSelectTopic={setSelectedTopic}
                />
              </div>

              {/* Right side: Persistent Topic Detail Panel */}
              <div className="lg:col-span-5 h-[420px] lg:h-full flex flex-col min-h-0 min-w-0">
                <TopicDetailPanel stat={selectedTopicStat} />
              </div>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
