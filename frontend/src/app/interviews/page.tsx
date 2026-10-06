"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getInterviews } from "@/services/interviewApi";
import { InterviewListItem } from "@/types/interview";
import { extractApiError } from "@/services/apiClient";
import { Search, CalendarDays, Briefcase, ChevronRight, User, CheckCircle2 } from "lucide-react";
import FilterSelect from "@/components/ui/FilterSelect";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function InterviewsListPage() {
  const authStatus = useRequireAuth();
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("NEWEST");

  useEffect(() => {
    if (authStatus !== "authed") return;
    async function loadData() {
      try {
        setLoading(true);
        const data = await getInterviews();
        setInterviews(data.items);
        setTotal(data.meta.total);
      } catch (error) {
        console.error("Failed to load interviews", error);
        console.error(extractApiError(error));
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [authStatus]);

  // Filtering Logic — failed/cancelled interviews are hidden
  const filteredInterviews = interviews.filter((item) => {
    const candidateName = (item.title || "").toLowerCase();
    const searchMatch = candidateName.includes(search.toLowerCase());
    const isVisible = item.status !== "FAILED" && item.status !== "CANCELLED";
    const decisionMatch =
      decisionFilter === "ALL" ||
      (decisionFilter === "NONE" && !item.hiring_decision) ||
      item.hiring_decision === decisionFilter;

    return searchMatch && isVisible && decisionMatch;
  });

  // Sorting Logic
  const sortedInterviews = [...filteredInterviews].sort((a, b) => {
    if (sortBy === "NEWEST") {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
    if (sortBy === "OLDEST") {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    }
    if (sortBy === "SCORE_HIGH") {
      const scoreA = parseFloat(a.overall_score || "0");
      const scoreB = parseFloat(b.overall_score || "0");
      return scoreB - scoreA;
    }
    if (sortBy === "SCORE_LOW") {
      const scoreA = parseFloat(a.overall_score || "0");
      const scoreB = parseFloat(b.overall_score || "0");
      return scoreA - scoreB;
    }
    return 0;
  });

  const getStatusBadge = (status: InterviewListItem["status"]) => {
    switch (status) {
      case "COMPLETED":
        return "bg-success-soft text-success border-success-border";
      case "PROCESSING":
      case "TRANSCRIBING":
        return "bg-info-soft text-info border-info-border animate-pulse";
      case "ANALYZING":
        return "bg-warning-soft text-warning border-warning-border animate-pulse";
      case "UPLOADED":
      default:
        return "bg-secondary/10 text-secondary/70 border-default";
    }
  };

  const getDecisionBadge = (decision: InterviewListItem["hiring_decision"]) => {
    switch (decision) {
      case "STRONG_HIRE":
        return "bg-success-soft text-success border-success-border font-bold";
      case "HIRE":
        return "bg-accent-soft text-primary border-accent-soft-border font-semibold";
      case "BORDERLINE":
        return "bg-warning-soft text-warning border-warning-border font-semibold";
      case "NO_HIRE":
        return "bg-danger-soft text-danger border-danger-border font-semibold";
      default:
        return "bg-surface-hover text-muted border-default font-medium";
    }
  };

  const getScoreBadgeClass = (scoreStr: string | null) => {
    if (!scoreStr) return "text-muted border-default bg-surface/50";
    const score = parseFloat(scoreStr);
    if (score >= 7.5) {
      return "text-success bg-success-soft border-success-border";
    }
    if (score >= 5.0) {
      return "text-warning bg-warning-soft border-warning-border";
    }
    return "text-danger bg-danger-soft border-danger-border";
  };

  return (
    <main className="py-6 sm:py-8 px-4 sm:px-6">
      <div className="mx-auto max-w-8xl space-y-6">

        {authStatus === "checking" && (
          <main className="flex min-h-[60vh] items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-secondary/50">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-soft-border border-t-secondary" />
              <span className="text-sm">Verifying your session…</span>
            </div>
          </main>
        )}

        {authStatus === "unauthed" && null}

        {/* Navigation / Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-default pb-5">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary">
              Interview Repository
            </h1>
            <p className="mt-1 text-sm sm:text-base text-secondary/60">
              Review and manage your analyzed candidates.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-card/90 px-3.5 py-1.5 text-xs font-semibold text-secondary shadow-sm border border-default">
              Total: {total ?? interviews.length} Interviews
            </span>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="rounded-2xl border border-default bg-card/80 p-4 sm:p-5 shadow-[var(--shadow)] backdrop-blur-xl">
          <div className="grid gap-3 sm:gap-4 md:grid-cols-3">
            {/* Search Input */}
            <div>
              <label htmlFor="search" className="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1.5">
                Search Candidate
              </label>
              <div className="relative flex items-center">
                <Search className="absolute left-3 h-3.5 w-3.5 text-muted pointer-events-none" />
                <input
                  id="search"
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by candidate or title..."
                  className="w-full rounded-xl border border-input-border bg-input-bg pl-8 pr-4 py-2 text-xs sm:text-sm text-input-text outline-none transition placeholder:text-input-placeholder focus:border-accent focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
            </div>

            {/* Hiring Decision Filter */}
            <div>
              <FilterSelect
                id="decision"
                label="Hiring Decision"
                value={decisionFilter}
                onChange={setDecisionFilter}
                placeholder="All Decisions"
                options={[
                  { value: "ALL", label: "All Decisions" },
                  { value: "STRONG_HIRE", label: "Strong Hire" },
                  { value: "HIRE", label: "Hire" },
                  { value: "BORDERLINE", label: "Borderline" },
                  { value: "NO_HIRE", label: "No Hire" },
                  { value: "NONE", label: "Unassigned" },
                ]}
              />
            </div>

            {/* Sort Order */}
            <div>
              <FilterSelect
                id="sorting"
                label="Sort By"
                value={sortBy}
                onChange={setSortBy}
                placeholder="Select sort order"
                options={[
                  { value: "NEWEST", label: "Newest Uploaded" },
                  { value: "OLDEST", label: "Oldest Uploaded" },
                  { value: "SCORE_HIGH", label: "Overall Score (High → Low)" },
                  { value: "SCORE_LOW", label: "Overall Score (Low → High)" },
                ]}
              />
            </div>
          </div>
        </div>

        {/* Dense Bordered Rows List */}
        {loading ? (
          <div className="rounded-2xl border border-default bg-card/70 overflow-hidden shadow-[var(--shadow)] divide-y divide-default/60">
            {[...Array(6)].map((_, index) => (
              <div key={index} className="animate-pulse flex items-center justify-between p-4 gap-4">
                <div className="h-5 w-48 rounded bg-accent-soft"></div>
                <div className="h-4 w-24 rounded bg-accent-soft hidden md:block"></div>
                <div className="h-4 w-24 rounded bg-accent-soft hidden sm:block"></div>
                <div className="h-5 w-20 rounded bg-accent-soft"></div>
                <div className="h-6 w-12 rounded bg-accent-soft"></div>
              </div>
            ))}
          </div>
        ) : sortedInterviews.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-default bg-card/70 p-12 text-center shadow-[var(--shadow)]">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft border border-accent-soft-border text-secondary mb-3">
              <Search className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-primary">No interviews found</h3>
            <p className="mt-1 text-xs text-secondary/60">
              Try adjusting your search query or filters.
            </p>
            <button
              onClick={() => {
                setSearch("");
                setDecisionFilter("ALL");
                setSortBy("NEWEST");
              }}
              className="mt-4 rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-2 text-xs font-semibold text-btn-primary-text shadow-[0_0_15px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="rounded-2xl border border-default bg-card/85 backdrop-blur-xl shadow-[var(--shadow)] overflow-hidden">
            {/* Table Header (Desktop) */}
            <div className="hidden md:grid grid-cols-12 gap-4 items-center border-b border-default bg-surface/60 px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted">
              <div className="col-span-4 flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-secondary" />
                <span>Candidate / Interview</span>
              </div>
              <div className="col-span-2 flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-secondary" />
                <span>Experience</span>
              </div>
              <div className="col-span-2 flex items-center gap-1.5">
                <CalendarDays className="h-3.5 w-3.5 text-secondary" />
                <span>Evaluated</span>
              </div>
              <div className="col-span-2 text-center">
                <span>Decision</span>
              </div>
              <div className="col-span-2 text-right">
                <span>Score & Action</span>
              </div>
            </div>

            {/* Dense Rows */}
            <div className="divide-y divide-default/60">
              {sortedInterviews.map((item) => {
                const displayName = item.title || `Interview #${item.id.slice(0, 8)}`;
                const displayDate = new Date(item.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                });
                const score = item.overall_score ? parseFloat(item.overall_score).toFixed(1) : "—";
                const experience = item.claimed_experience_years
                  ? `${parseFloat(item.claimed_experience_years)} yrs`
                  : "—";

                return (
                  <Link
                    key={item.id}
                    href={`/interviews/${item.id}`}
                    className="group block px-4 py-3 sm:px-5 sm:py-3.5 transition-all duration-150 hover:bg-surface-hover/80 focus:outline-none focus-visible:bg-surface-hover"
                  >
                    {/* Desktop layout: Grid */}
                    <div className="hidden md:grid grid-cols-12 gap-4 items-center">
                      {/* Candidate Name + Status */}
                      <div className="col-span-4 min-w-0 flex items-center gap-2.5">
                        <span
                          className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold border uppercase tracking-wider ${getStatusBadge(
                            item.status
                          )}`}
                        >
                          {item.status === "COMPLETED" ? "Ready" : item.status}
                        </span>
                        <h3 className="text-sm font-semibold text-primary group-hover:text-secondary transition-colors truncate" title={displayName}>
                          {displayName}
                        </h3>
                      </div>

                      {/* Experience */}
                      <div className="col-span-2 text-xs text-secondary/80 font-medium">
                        {experience}
                      </div>

                      {/* Evaluated Date */}
                      <div className="col-span-2 text-xs text-secondary/70">
                        {displayDate}
                      </div>

                      {/* Hiring Decision */}
                      <div className="col-span-2 text-center">
                        {item.status === "COMPLETED" ? (
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs border tracking-wide ${getDecisionBadge(
                              item.hiring_decision
                            )}`}
                          >
                            {item.hiring_decision ? item.hiring_decision.replace("_", " ") : "PENDING"}
                          </span>
                        ) : (
                          <span className="text-xs text-muted italic">Processing</span>
                        )}
                      </div>

                      {/* Overall Score + Action */}
                      <div className="col-span-2 flex items-center justify-end gap-3">
                        <span
                          className={`inline-flex items-center justify-center min-w-[42px] px-2 py-0.5 rounded-lg text-xs font-bold border ${getScoreBadgeClass(
                            item.overall_score
                          )}`}
                        >
                          {score}
                        </span>
                        <span className="inline-flex items-center text-xs font-semibold text-secondary group-hover:text-primary transition-colors gap-1">
                          <span className="hidden lg:inline">Report</span>
                          <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                        </span>
                      </div>
                    </div>

                    {/* Mobile layout: Compact stacked row */}
                    <div className="md:hidden flex items-center justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold border uppercase ${getStatusBadge(
                              item.status
                            )}`}
                          >
                            {item.status === "COMPLETED" ? "Ready" : item.status}
                          </span>
                          {item.hiring_decision && (
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] border font-bold ${getDecisionBadge(
                                item.hiring_decision
                              )}`}
                            >
                              {item.hiring_decision.replace("_", " ")}
                            </span>
                          )}
                        </div>
                        <h3 className="text-sm font-semibold text-primary truncate" title={displayName}>
                          {displayName}
                        </h3>
                        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-secondary/60">
                          <span>{displayDate}</span>
                          <span>•</span>
                          <span>{experience}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span
                          className={`inline-flex items-center justify-center px-2 py-0.5 rounded-lg text-xs font-bold border ${getScoreBadgeClass(
                            item.overall_score
                          )}`}
                        >
                          {score}
                        </span>
                        <ChevronRight className="h-4 w-4 text-muted group-hover:text-primary transition-colors" />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </main>
  );
}