"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  HelpCircle,
  MessageSquare,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Layers,
} from "lucide-react";
import { getTopicQuestions } from "@/services/dashboardApi";
import type { TopicQuestionItem, TopicQuestionsResponse } from "@/types/dashboard";
import { extractApiError } from "@/services/apiClient";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { GlassCard } from "@/components/landing/MockPanels";
import FilterSelect from "@/components/ui/FilterSelect";

interface PageProps {
  params: Promise<{ topic: string }>;
}

const PAGE_SIZE = 20;

export default function TopicQuestionsPage({ params }: PageProps) {
  const { topic: rawTopic } = use(params);
  const topic = decodeURIComponent(rawTopic);
  const authStatus = useRequireAuth();

  const [questionsData, setQuestionsData] = useState<TopicQuestionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [sort, setSort] = useState<"recent" | "score">("recent");
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (authStatus !== "authed") return;

    async function loadQuestions() {
      try {
        setLoading(true);
        setError(null);
        const res = await getTopicQuestions(topic, {
          limit: PAGE_SIZE,
          offset,
          sort,
        });
        setQuestionsData(res);
      } catch (err) {
        console.error("Failed to load topic questions:", err);
        setError(extractApiError(err));
      } finally {
        setLoading(false);
      }
    }

    loadQuestions();
  }, [authStatus, topic, offset, sort]);

  // Reset pagination when sort changes
  const handleSortChange = (newSort: string) => {
    setSort(newSort as "recent" | "score");
    setOffset(0);
  };

  const toggleQuestion = (id: string) => {
    setExpandedIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

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

  const total = questionsData?.total ?? 0;
  const questions = questionsData?.questions ?? [];
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const startItem = total === 0 ? 0 : offset + 1;
  const endItem = Math.min(offset + PAGE_SIZE, total);

  const getDifficultyBadge = (difficulty: string | null) => {
    if (!difficulty) return null;
    const lower = difficulty.toLowerCase();
    let badgeStyle = "bg-secondary/10 text-secondary border-default";
    if (lower === "easy") {
      badgeStyle = "bg-success-soft text-success border-success-border";
    } else if (lower === "medium") {
      badgeStyle = "bg-warning-soft text-warning border-warning-border";
    } else if (lower === "hard") {
      badgeStyle = "bg-danger-soft text-danger border-danger-border";
    }

    return (
      <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider ${badgeStyle}`}>
        {difficulty}
      </span>
    );
  };

  return (
    <main className="py-6 sm:py-8 px-4 sm:px-6">
      <div className="mx-auto max-w-8xl space-y-6">
        {/* Breadcrumb Back Link */}
        <div>
          <Link
            href="/analytics"
            className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted hover:text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Analytics Overview</span>
          </Link>
        </div>

        {/* Header with Title & Stats */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-default pb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted mb-1">
              <Layers className="h-3.5 w-3.5 text-secondary" />
              <span>Topic Drill-Down</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary">
              {topic}
            </h1>
            <p className="mt-1.5 text-sm sm:text-base text-secondary/70">
              Review all questions asked for this topic, with candidate responses, scores, and concept assessments.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full bg-card/90 px-3.5 py-1.5 text-xs font-semibold text-secondary shadow-sm border border-default">
              <HelpCircle className="h-3.5 w-3.5 text-secondary/70" />
              {total} {total === 1 ? "Question Total" : "Questions Total"}
            </span>
          </div>
        </div>

        {/* Controls Row: Sort & Summary */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-default bg-card/80 p-4 shadow-[var(--shadow)] backdrop-blur-xl">
          <div className="text-xs text-secondary/70 font-medium">
            {total > 0 ? (
              <span>
                Showing <strong className="text-primary">{startItem}</strong>–<strong className="text-primary">{endItem}</strong> of{" "}
                <strong className="text-primary">{total}</strong> questions
              </span>
            ) : (
              <span>No questions to display</span>
            )}
          </div>

          <div className="w-full sm:w-56">
            <FilterSelect
              id="sort-select"
              value={sort}
              onChange={handleSortChange}
              options={[
                { value: "recent", label: "Most Recent" },
                { value: "score", label: "Score (High → Low)" },
              ]}
              placeholder="Sort by..."
            />
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="rounded-2xl border border-danger/20 bg-danger-soft p-4 text-sm text-danger flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Loading Skeletons */}
        {loading && (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-28 rounded-2xl bg-surface-hover/60 border border-default" />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && questions.length === 0 && (
          <GlassCard className="p-12 text-center max-w-xl mx-auto my-12">
            <div className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-accent-soft text-secondary border border-accent-soft-border mb-4">
              <HelpCircle className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-bold text-primary mb-2">
              No Questions Found
            </h2>
            <p className="text-sm text-secondary/70 mb-6">
              There are currently no interview questions recorded under the topic &ldquo;{topic}&rdquo;.
            </p>
            <Link
              href="/analytics"
              className="inline-flex items-center gap-2 rounded-xl border border-default bg-surface/80 px-4 py-2 text-sm font-semibold text-secondary hover:text-primary transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Overview</span>
            </Link>
          </GlassCard>
        )}

        {/* Questions List */}
        {!loading && questions.length > 0 && (
          <div className="space-y-4">
            {questions.map((q: TopicQuestionItem, idx) => {
              const itemKey = q.id || `q-${idx}`;
              const isExpanded = !!expandedIds[itemKey];
              const scoreVal = q.average_score ? parseFloat(q.average_score) : null;

              return (
                <GlassCard
                  key={itemKey}
                  className="transition-all duration-200 border-default hover:border-accent-soft-border overflow-hidden"
                >
                  {/* Collapsed Header / Trigger */}
                  <button
                    type="button"
                    onClick={() => toggleQuestion(itemKey)}
                    className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-4 hover:bg-surface-hover/40 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <span className="shrink-0 flex h-7 w-7 items-center justify-center rounded-lg bg-surface border border-default text-xs font-bold text-secondary">
                        #{q.question_number || idx + 1 + offset}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm sm:text-base font-semibold text-primary leading-snug">
                          {q.question}
                        </p>

                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          {getDifficultyBadge(q.difficulty)}

                          {q.strong_concepts && q.strong_concepts.length > 0 && (
                            <span className="text-[11px] text-success font-medium inline-flex items-center gap-1">
                              <CheckCircle2 className="h-3 w-3" />
                              {q.strong_concepts.length} {q.strong_concepts.length === 1 ? "strength" : "strengths"}
                            </span>
                          )}

                          {q.weak_concepts && q.weak_concepts.length > 0 && (
                            <span className="text-[11px] text-warning font-medium inline-flex items-center gap-1">
                              <AlertCircle className="h-3 w-3" />
                              {q.weak_concepts.length} {q.weak_concepts.length === 1 ? "gap" : "gaps"}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {scoreVal !== null ? (
                        <div className="text-right">
                          <span className="inline-flex items-center justify-center rounded-xl bg-accent-soft border border-accent-soft-border px-2.5 py-1 text-xs font-bold text-secondary">
                            {scoreVal.toFixed(1)} / 10
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted">—</span>
                      )}

                      <div className="p-1 rounded-lg text-muted hover:text-primary">
                        {isExpanded ? (
                          <ChevronDown className="h-5 w-5" />
                        ) : (
                          <ChevronRight className="h-5 w-5" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded Content Drawer */}
                  {isExpanded && (
                    <div className="border-t border-default bg-surface/30 p-4 sm:p-6 space-y-4 text-xs sm:text-sm animate-[fadeIn_0.2s_ease]">
                      {/* Candidate Answer */}
                      <div>
                        <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted mb-2">
                          <MessageSquare className="h-3.5 w-3.5 text-secondary" />
                          Candidate Answer
                        </h4>
                        <div className="rounded-xl border border-default bg-surface/60 p-4 text-secondary leading-relaxed whitespace-pre-wrap">
                          {q.answer || <span className="italic text-muted">No answer recorded.</span>}
                        </div>
                      </div>

                      {/* Feedback */}
                      {q.feedback && (
                        <div>
                          <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted mb-2">
                            <Sparkles className="h-3.5 w-3.5 text-secondary" />
                            Evaluation Feedback
                          </h4>
                          <div className="rounded-xl border border-accent-soft-border bg-accent-soft/40 p-4 text-secondary leading-relaxed">
                            {q.feedback}
                          </div>
                        </div>
                      )}

                      {/* Concept Badges / Tags */}
                      {((q.strong_concepts && q.strong_concepts.length > 0) ||
                        (q.weak_concepts && q.weak_concepts.length > 0)) && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                          {q.strong_concepts && q.strong_concepts.length > 0 && (
                            <div>
                              <h5 className="text-[11px] font-semibold uppercase tracking-wider text-success mb-2 flex items-center gap-1.5">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                Demonstrated Strengths
                              </h5>
                              <div className="flex flex-wrap gap-1.5">
                                {q.strong_concepts.map((concept, cIdx) => (
                                  <span
                                    key={cIdx}
                                    className="inline-flex items-center gap-1 rounded-full border border-success-border bg-success-soft px-2.5 py-1 text-xs font-medium text-success"
                                  >
                                    <span className="h-1.5 w-1.5 rounded-full bg-success" />
                                    {concept}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {q.weak_concepts && q.weak_concepts.length > 0 && (
                            <div>
                              <h5 className="text-[11px] font-semibold uppercase tracking-wider text-warning mb-2 flex items-center gap-1.5">
                                <AlertCircle className="h-3.5 w-3.5" />
                                Areas for Improvement
                              </h5>
                              <div className="flex flex-wrap gap-1.5">
                                {q.weak_concepts.map((concept, cIdx) => (
                                  <span
                                    key={cIdx}
                                    className="inline-flex items-center gap-1 rounded-full border border-warning-border bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning"
                                  >
                                    <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                                    {concept}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </GlassCard>
              );
            })}
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-default pt-6">
            <button
              type="button"
              onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              disabled={offset === 0}
              className="inline-flex items-center gap-2 rounded-xl border border-default bg-surface/70 px-4 py-2 text-xs font-semibold text-secondary transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:enabled:bg-surface-hover hover:enabled:text-primary"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Previous</span>
            </button>

            <span className="text-xs font-semibold text-secondary">
              Page {currentPage} of {totalPages}
            </span>

            <button
              type="button"
              onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
              disabled={offset + PAGE_SIZE >= total}
              className="inline-flex items-center gap-2 rounded-xl border border-default bg-surface/70 px-4 py-2 text-xs font-semibold text-secondary transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:enabled:bg-surface-hover hover:enabled:text-primary"
            >
              <span>Next</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
