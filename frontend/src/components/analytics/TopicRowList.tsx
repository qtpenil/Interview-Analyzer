"use client";

import { useState } from "react";
import { ChevronRight, Clock, FileText, BarChart, Search, X } from "lucide-react";
import type { TopicStat } from "@/types/dashboard";
import { timeAgo } from "@/utils/time";

interface TopicRowListProps {
  topics: TopicStat[];
  selectedTopic: string | null;
  onSelectTopic: (topic: string) => void;
}

export function TopicRowList({
  topics,
  selectedTopic,
  onSelectTopic,
}: TopicRowListProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTopics = topics.filter((t) =>
    t.topic.toLowerCase().includes(searchQuery.trim().toLowerCase())
  );

  const getScoreBadgeStyle = (score: number) => {
    if (score >= 7.5) {
      return "text-success bg-success-soft border-success-border";
    }
    if (score >= 5.0) {
      return "text-warning bg-warning-soft border-warning-border";
    }
    return "text-danger bg-danger-soft border-danger-border";
  };

  return (
    <div className="flex flex-col h-full min-w-0 rounded-3xl border border-default bg-card/85 backdrop-blur-xl overflow-hidden">
      {/* Search / Filter Bar */}
      <div className="p-3 sm:px-4 border-b border-default bg-surface/40 flex items-center gap-2 shrink-0">
        <div className="relative flex-1 flex items-center">
          <Search className="absolute left-3 h-3.5 w-3.5 text-muted pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter topics..."
            className="w-full rounded-xl border border-default bg-surface/70 pl-8 pr-7 py-1.5 text-xs text-primary placeholder:text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              aria-label="Clear filter"
              className="absolute right-2.5 p-0.5 rounded-md text-muted hover:text-primary transition-colors"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        <span className="text-[11px] font-semibold text-muted shrink-0 px-2 py-1 rounded-lg bg-surface/60 border border-default">
          {searchQuery ? `${filteredTopics.length} of ${topics.length}` : `${topics.length} topics`}
        </span>
      </div>

      {/* Table-like header */}
      <div className="flex items-center justify-between gap-3 border-b border-default bg-surface/60 px-5 py-2.5 text-[10px] font-semibold uppercase tracking-wider text-muted shrink-0 min-w-0 overflow-hidden">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <BarChart className="h-3 w-3 text-secondary shrink-0" />
          <span className="truncate">Topic Name & Activity</span>
        </div>
        <div className="flex items-center gap-6 sm:gap-10 shrink-0">
          <span className="hidden sm:inline">Score Range</span>
          <span>Avg Score</span>
        </div>
      </div>

      {/* Scrollable List — flex-1 min-h-0 fills remaining vertical space */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden divide-y divide-default/60">
        {filteredTopics.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted space-y-2">
            <p>No topics matching &ldquo;{searchQuery}&rdquo;</p>
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="text-[11px] text-secondary underline hover:text-primary"
            >
              Clear filter
            </button>
          </div>
        ) : (
          filteredTopics.map((stat) => {
            const isSelected = selectedTopic === stat.topic;
            const avgScore = parseFloat(stat.average_score || "0");
            const highestScore = stat.highest_score
              ? parseFloat(stat.highest_score).toFixed(1)
              : "—";
            const lowestScore = stat.lowest_score
              ? parseFloat(stat.lowest_score).toFixed(1)
              : "—";

            return (
              <button
                key={stat.topic}
                type="button"
                onClick={() => onSelectTopic(stat.topic)}
                aria-current={isSelected}
                className={`w-full text-left flex items-center justify-between gap-4 px-5 py-3 transition-all duration-150 group relative focus:outline-none focus-visible:bg-surface-hover ${
                  isSelected
                    ? "bg-accent-soft text-primary font-medium"
                    : "text-secondary hover:bg-surface-hover/80 hover:text-primary"
                }`}
              >
                {/* Left active accent line */}
                {isSelected && (
                  <span
                    aria-hidden="true"
                    className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-gradient-to-b from-btn-primary-from to-btn-primary-to shadow-[0_0_12px_var(--shadow-glow)]"
                  />
                )}

                {/* Topic Information */}
                <div className="min-w-0 flex-1 pl-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs sm:text-sm truncate font-semibold transition-colors ${
                        isSelected ? "text-primary" : "text-primary/90 group-hover:text-primary"
                      }`}
                    >
                      {stat.topic}
                    </span>
                  </div>

                  {/* Subtitle / Metadata */}
                  <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[10px] sm:text-[11px] text-secondary/60">
                    <span className="inline-flex items-center gap-1">
                      <FileText className="h-2.5 w-2.5 text-muted" />
                      {stat.interview_count} {stat.interview_count === 1 ? "interview" : "interviews"}
                    </span>
                    <span>•</span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5 text-muted" />
                      {timeAgo(stat.last_assessed_at)}
                    </span>
                  </div>
                </div>

                {/* Right: Score metrics */}
                <div className="flex items-center gap-3 sm:gap-6 shrink-0">
                  {/* Score Range (Best / Lowest) */}
                  <div className="hidden sm:flex flex-col items-end text-[10px] text-secondary/70">
                    <span className="text-[9px] text-muted font-medium">Range</span>
                    <span className="font-mono font-medium">
                      {lowestScore} – {highestScore}
                    </span>
                  </div>

                  {/* Average Score Pill */}
                  <div className="flex items-center gap-1.5 sm:gap-2">
                    <span
                      className={`inline-flex items-center justify-center min-w-[38px] px-2 py-0.5 rounded-lg text-xs font-bold border transition-colors ${getScoreBadgeStyle(
                        avgScore
                      )}`}
                    >
                      {avgScore.toFixed(1)}
                    </span>
                    <ChevronRight
                      className={`h-3.5 w-3.5 transition-transform duration-150 ${
                        isSelected
                          ? "text-primary translate-x-0.5"
                          : "text-muted/50 group-hover:text-secondary group-hover:translate-x-0.5"
                      }`}
                    />
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
