"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import { getInterviewDetail, downloadReport } from "@/services/interviewApi";
import { InterviewDetail, InterviewTopic, InterviewQuestion } from "@/types/interview";
import {
  ArrowLeft,
  Download,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  FileText,
  Clock,
  User,
  X,
  Zap,
  Activity,
  AlertCircle,
  Layers,
} from "lucide-react";
import { GlassCard, InsightChip } from "@/components/landing/MockPanels";
import { ScoreRing } from "@/components/common/ScoreRing";
import { useRequireAuth } from "@/hooks/useRequireAuth";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function InterviewDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const authStatus = useRequireAuth();
  const [detail, setDetail] = useState<InterviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [openTopic, setOpenTopic] = useState<string | null>(null);
  const [selectedQIdx, setSelectedQIdx] = useState(0);
  const modalTopic = openTopic
    ? detail?.topics.find((t) => t.topic === openTopic) ?? null
    : null;

  const modalTopicQuestions =
    modalTopic?.questions && modalTopic.questions.length > 0
      ? modalTopic.questions
      : detail?.questions?.filter(
          (q) =>
            (q.category || "").trim().toLowerCase() ===
            (modalTopic?.topic || "").trim().toLowerCase()
        ) || [];

  const selectedIdx =
    modalTopicQuestions.length === 0
      ? 0
      : Math.min(selectedQIdx, modalTopicQuestions.length - 1);
  const selectedQ = modalTopicQuestions[selectedIdx] ?? null;

  const handleConceptClick = (questionIds?: string[]) => {
    if (!questionIds || questionIds.length === 0 || modalTopicQuestions.length === 0) return;
    const idx = modalTopicQuestions.findIndex(
      (q, i) =>
        questionIds.includes(q.id) ||
        (q.question_number !== undefined && questionIds.includes(String(q.question_number))) ||
        questionIds.includes(String(i + 1))
    );
    setSelectedQIdx(idx >= 0 ? idx : 0);
  };

  useEffect(() => {
    if (!openTopic) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenTopic(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openTopic]);

  // Reset the selected question when a different topic modal opens
  // (render-time adjustment — endorsed over setState-in-effect).
  const [prevOpenTopic, setPrevOpenTopic] = useState(openTopic);
  if (prevOpenTopic !== openTopic) {
    setPrevOpenTopic(openTopic);
    setSelectedQIdx(0);
  }

  useEffect(() => {
    if (authStatus !== "authed") return;
    let active = true;

    async function loadDetail() {
      try {
        setLoading(true);
        const data = await getInterviewDetail(id);
        if (!active) return;
        setDetail(data);
      } catch (error) {
        console.error("Failed to load interview details", error);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDetail();

    // Poll while interview is being processed
    const poll = setInterval(async () => {
      try {
        const data = await getInterviewDetail(id);
        if (!active || !data) return;
        setDetail(data);
        // Stop polling when terminal
        if (data.status === "COMPLETED" || data.status === "FAILED" || data.status === "CANCELLED") {
          clearInterval(poll);
        }
      } catch {
        clearInterval(poll);
      }
    }, 4000);

    return () => {
      active = false;
      clearInterval(poll);
    };
  }, [id, authStatus]);

  if (authStatus === "checking" || loading) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-8xl">
          <div className="animate-pulse mb-8">
            <div className="h-4 w-24 bg-accent-soft rounded mb-4"></div>
            <div className="h-8 w-1/3 bg-accent-soft rounded mb-2"></div>
            <div className="h-4 w-1/4 bg-accent-soft rounded"></div>
          </div>
          <div className="grid gap-8 lg:grid-cols-3">
<div className="lg:col-span-2 space-y-6">
              <div className="h-64 bg-card/70 border border-default rounded-2xl p-6 animate-pulse"></div>
              <div className="h-96 bg-card/70 border border-default rounded-2xl p-6 animate-pulse"></div>
            </div>
            <div className="space-y-6">
              <div className="h-80 bg-card/70 border border-default rounded-2xl p-6 animate-pulse"></div>
              <div className="h-48 bg-card/70 border border-default rounded-2xl p-6 animate-pulse"></div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (authStatus === "unauthed") {
    return null;
  }

  if (!detail) {
    return (
      <main className="min-h-screen flex flex-col justify-center items-center px-4 py-8 sm:px-6">
        <div className="text-center bg-card/90 backdrop-blur-xl border border-default rounded-2xl p-10 max-w-md shadow-[var(--shadow)]">
          <AlertCircle className="mx-auto h-12 w-12 text-danger mb-4" />
          <h2 className="text-2xl font-bold text-primary mb-2 font-geist">Report Not Found</h2>
          <p className="text-secondary/50 mb-6">
            The interview report you are looking for does not exist or has been deleted.
          </p>
          <Link
            href="/interviews"
            className="inline-flex items-center rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-2.5 text-sm font-semibold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from transition"
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> Return to Repository
          </Link>
        </div>
      </main>
    );
  }

  // ----------------------------------------------------
  // Processing Pipeline View (For UPLOADED, PROCESSING, TRANSCRIBING, ANALYZING)
  // ----------------------------------------------------
  if (detail.status !== "COMPLETED") {

    // CANCELLED — simple status card, no pipeline
    if (detail.status === "CANCELLED") {
      return (
<main className="py-4 sm:py-5 px-1 sm:px-5 font-geist">
          <div className="mx-auto max-w-4xl">
            <div className="mb-8">
              <Link
                href="/interviews"
                className="inline-flex items-center text-sm font-medium text-secondary transition hover:text-primary"
              >
                <ArrowLeft className="mr-1 h-4 w-4" /> Back to Repository
              </Link>
              <div className="mt-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-extrabold text-primary">{detail.title || "Interview Candidate"}</h1>
                  <p className="mt-1 text-sm text-muted">ID: {detail.id}</p>
                </div>
                <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-warning-soft text-warning border border-warning-border">
                  CANCELLED
                </span>
              </div>
            </div>
            <GlassCard className="p-6 sm:p-8">
              <div className="flex flex-col items-center gap-4 py-8 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-warning-soft border border-warning-border text-warning">
                  <AlertCircle className="h-8 w-8" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-primary">Interview Cancelled</h2>
                  <p className="mt-2 text-sm text-secondary/60 max-w-md">
                    The processing was cancelled before it could complete. No analysis results are available.
                  </p>
                </div>
                <Link
                  href="/dashboard"
                  className="mt-4 inline-flex items-center rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-6 py-3 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
                >
                  Upload a New Interview
                </Link>
              </div>
            </GlassCard>
          </div>
        </main>
      );
    }

    // The backend can emit more granular statuses (e.g. "Analyzing Questions",
    // "Generating Insights", "Creating PDF"). We collapse them into the 5 stages
    // shown in the UI so the pipeline only ever displays:
    //   Uploading · Preparing Audio · Transcribing · Analyzing with AI · Completed
    const STAGE_KEYS = ["UPLOADED", "PROCESSING", "TRANSCRIBING", "ANALYZING", "COMPLETED"];
    const STAGE_LABELS = [
      "Uploading",
      "Preparing Audio",
      "Transcribing",
      "Analyzing with AI",
      "Completed",
    ];
    const STAGE_DESCS = [
      "Your interview file is being uploaded",
      "Extracting and preparing the audio track",
      "Converting speech into a written transcript",
      "Evaluating responses and generating insights",
      "Your report is ready to view",
    ];

    // Map any backend status string to one of the 5 displayed stages.
    const getStageIndex = (status?: string | null): number => {
      const s = (status || "").toLowerCase();
      if (s.includes("upload")) return 0;
      if (s.includes("audio") || s.includes("prepar") || s.includes("process")) return 1;
      if (s.includes("transcrib")) return 2;
      if (
        s.includes("analyz") ||
        s.includes("generat") ||
        s.includes("insight") ||
        s.includes("pdf") ||
        s.includes("report") ||
        s.includes("question")
      ) return 3;
      if (s.includes("complet")) return 4;
      return -1;
    };

    const currentStage = getStageIndex(detail.status);

    const steps = STAGE_KEYS.map((key, index) => ({
      key,
      title: STAGE_LABELS[index],
      desc: STAGE_DESCS[index],
      active: currentStage >= index,
      current: currentStage === index,
    }));

    const getPipelineStatusText = (status: string) => {
      if (status === "FAILED") return "Pipeline process failed.";
      const idx = getStageIndex(status);
      switch (idx) {
        case 0: return "Uploading your interview file...";
        case 1: return "Preparing audio track...";
        case 2: return "Transcribing speech to text...";
        case 3: return "Analyzing with AI...";
        case 4: return "Finalizing your report...";
        default: return "In Progress...";
      }
    };

    return (
      <main className="py-6 sm:py-8 px-2 sm:px-6 font-geist">
        <div className="mx-auto max-w-4xl">

          <div className="mb-8">
            <Link
              href="/interviews"
              className="inline-flex items-center text-sm font-medium text-secondary transition hover:text-primary"
            >
              <ArrowLeft className="mr-1 h-4 w-4" /> Back to Repository
            </Link>

              <div className="mt-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-extrabold text-primary">{detail.title || "Interview Candidate"}</h1>
                </div>
                <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${detail.status === "FAILED" ? "bg-danger-soft text-danger border border-danger-border" : "bg-accent-soft text-secondary border border-accent-soft-border animate-pulse"
                  }`}>
                  {currentStage >= 0 ? STAGE_LABELS[currentStage] : "Failed"}
                </span>
              </div>
          </div>

          <GlassCard className="p-6 sm:p-8">
            <div className="flex flex-col md:flex-row items-center gap-6 justify-between border-b border-default pb-6 mb-8">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft border border-accent-soft-border text-secondary">
                  {detail.status === "FAILED" ? <AlertCircle className="h-6 w-6 text-danger" /> : <Activity className="h-6 w-6 animate-spin text-secondary" />}
                </div>
                <div>
                  <h3 className="font-bold text-primary">
                    {detail.status === "FAILED" ? "Processing Failed" : "Analyzing Interview Video"}
                  </h3>
                  <p className="text-sm text-secondary/50 mt-0.5">
                    {getPipelineStatusText(detail.status)}
                  </p>
                </div>
              </div>
            </div>

            {/* Stepper Pipeline */}
            <div className="relative pl-6 md:pl-0">
              <div className="absolute left-2.5 md:left-1/2 top-4 bottom-4 w-0.5 bg-accent-soft -translate-x-1/2 hidden md:block"></div>

              <div className="space-y-8 md:space-y-12">
                {steps.map((step, idx) => {
                  const isCurrent = step.current;
                  return (
                    <div key={idx} className="relative flex flex-col md:flex-row items-start md:items-center">

                      {/* Left: Desktop Title */}
                      <div className="md:w-1/2 md:pr-12 md:text-right hidden md:block">
                        <h4 className={`text-md font-bold ${step.active ? "text-primary" : "text-muted"}`}>
                          {step.title}
                        </h4>
                      </div>

                      {/* Middle Badge Marker */}
                      <div className="absolute left-0 md:left-1/2 flex items-center justify-center -translate-x-1/2 z-10">
                        <div className={`flex h-6 w-6 items-center justify-center rounded-full border-2 transition-all ${isCurrent
                            ? "bg-gradient-to-br from-btn-primary-from to-btn-primary-to border-accent scale-125 text-btn-primary-text ring-4 ring-[var(--ring)]"
                            : step.active
                              ? "bg-accent-soft border-accent-soft-border text-secondary"
                              : "bg-black/30 border-default text-muted"
                          }`}>
                          {isCurrent ? (
                            <Zap className="h-3 w-3 animate-pulse fill-current" />
                          ) : step.active ? (
                            <CheckCircle className="h-3.5 w-3.5 fill-current" />
                          ) : (
                            <div className="h-1.5 w-1.5 rounded-full bg-muted"></div>
                          )}
                        </div>
                      </div>

                      {/* Right: Desktop Desc & Mobile Title */}
                      <div className="pl-8 md:pl-12 md:w-1/2">
                        <h4 className={`text-md font-bold md:hidden block ${step.active ? "text-primary" : "text-muted"}`}>
                          {step.title}
                        </h4>
                        <p className={`text-sm mt-0.5 ${step.active ? "text-secondary/60" : "text-muted"}`}>
                          {step.desc}
                        </p>
                      </div>

                    </div>
                  );
                })}
              </div>
            </div>

            {detail.status === "FAILED" && (
              <div className="mt-8 rounded-2xl bg-danger-soft border border-danger-border p-4 flex gap-3 text-danger">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-danger" />
                <div>
                  <h4 className="font-bold">Processing Failed</h4>
                  <p className="text-sm mt-1">
                    {detail.failure_reason || detail.reason || "The interview could not be processed. Please check the file format and try uploading again."}
                  </p>
                  <Link
                    href="/dashboard"
                    className="mt-3 inline-flex items-center text-xs font-bold uppercase tracking-wider text-danger hover:text-danger transition"
                  >
                    Upload a New Interview
                  </Link>
                </div>
              </div>
            )}
          </GlassCard>
        </div>
      </main>
    );
  }

  // ----------------------------------------------------
  // Completed Details View
  // ----------------------------------------------------
  const displayDate = new Date(detail.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });

  // One uniform, theme-driven badge style for every decision — the label
  // carries the meaning, the color always follows the project theme.
  const DECISION_BADGE =
    "bg-gradient-to-r from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-sm";

  const getDecisionLabel = (decision: InterviewDetail["hiring_decision"]) => {
    switch (decision) {
      case "STRONG_HIRE":
        return "Strong Hire Recommended";
      case "HIRE":
        return "Hiring Recommended";
      case "BORDERLINE":
        return "Borderline Fit";
      case "NO_HIRE":
        return "Do Not Hire";
      default:
        return "Decision Pending";
    }
  };

  const decisionLabel = detail.hiring_decision ? getDecisionLabel(detail.hiring_decision) : "Decision Pending";

  const formatScoreLabel = (scoreStr: string | null | undefined) => {
    return scoreStr ? parseFloat(scoreStr).toFixed(2) : "N/A";
  };

  return (
    <main className="py-3 sm:py-4 px-4 sm:px-6 font-geist">
      <div className="mx-auto max-w-8xl">

        {/* Dashboard Grid */}
        <div className="grid gap-6 lg:grid-cols-3">

          {/* Row 1, Left: Hero Dashboard Card (2/3 width) */}
          <div className="lg:col-span-2">
            <GlassCard className="overflow-hidden">
              <div className="flex flex-col gap-5 border-b border-default bg-surface/40 p-5 pb-3 sm:p-6 sm:pb-4 md:flex-row md:items-start md:justify-between">
                <div className="max-w-md">
                  <Link
                    href="/interviews"
                    className="group inline-flex items-center text-sm font-medium text-secondary transition hover:text-primary"
                  >
                    <ArrowLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-0.5" /> Back to Repository
                  </Link>
                  <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-primary">
                    {detail.title || "Interview Candidate"}
                  </h1>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-secondary/50">
                    <span className="flex items-center gap-1.5"><Clock className="h-4 w-4 text-muted" /> {displayDate}</span>
                    <span className="hidden xl:inline text-border-strong">|</span>
                    <span className="flex items-center gap-1.5"><User className="h-4 w-4 text-muted" /> {detail.claimed_experience_years ? `${parseFloat(detail.claimed_experience_years)} Years Exp.` : "Exp. Unspecified"}</span>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <span className={`inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-bold uppercase tracking-wider ${DECISION_BADGE}`}>
                      {decisionLabel}
                    </span>
                    <button
                      onClick={() => downloadReport(id as string)}
                      className="inline-flex items-center rounded-xl border border-default bg-surface/40 px-4 py-2 text-sm font-semibold text-secondary shadow-sm transition hover:border-accent-soft-border hover:bg-accent-soft"
                    >
                      <Download className="mr-2 h-4 w-4" /> Download PDF Report
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-5">
                  <ScoreRing value={ parseFloat(detail.overall_score || "0") } size={110} stroke={9} label="Overall" strokeColor="var(--accent)" />
                </div>
              </div>

              {/* Quick insight chips */}
              <div className="flex flex-wrap items-center gap-2 px-5 pt-2 pb-3 sm:px-6">
                <span className="text-[11px] font-bold uppercase tracking-widest text-muted">Highlights</span>
                {detail.topics.slice(0, 3).map((t) => (
                  <InsightChip key={t.topic}>{t.topic}</InsightChip>
                ))}
                <InsightChip>
                  {parseFloat(detail.overall_score || "0") >= 8.0 ? "Strong candidate signal" : parseFloat(detail.overall_score || "0") >= 5.0 ? "Average performance" : "Needs review"}
                </InsightChip>
              </div>
            </GlassCard>
          </div>

          {/* Row 1, Right: Sidebar Metrics (1/3 width) */}
          <div className="order-first lg:order-none">
            <div className="lg:sticky lg:top-6">
              <GlassCard className="p-5 sm:p-6">
                {/* Breakdown Sliders */}
                <div className="space-y-4">
                  {[
                    { label: "Technical Score", val: detail.technical_score },
                    { label: "Communication Skills", val: detail.communication_score },
                    { label: "Confidence Rating", val: detail.confidence_score },
                    { label: "Knowledge Depth", val: detail.knowledge_depth },
                    { label: "Experience Alignment", val: detail.experience_alignment_score }
                   ].map((bar, idx) => {
                     const scoreFloat = parseFloat(bar.val || "0");
                     const barColor = "bg-gradient-to-r from-btn-primary-from to-btn-primary-to";
                     return (
                      <div key={idx}>
                        <div className="flex justify-between text-xs font-semibold text-muted uppercase mb-1.5">
                          <span>{bar.label}</span>
                          <span className="font-bold text-primary">{formatScoreLabel(bar.val)}</span>
                        </div>
                        <div className="h-1.5 w-full bg-black/30 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${barColor} rounded-full`}
                            style={{ width: `${scoreFloat * 10}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </div>
          </div>

          {/* Row 2: Topics Covered Section — now spans the full width */}
          <div className="lg:col-span-3">
            <GlassCard className="p-5 sm:p-6">
              <div className="flex items-center gap-4 mb-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft border border-accent-soft-border text-secondary">
                  <Layers className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-primary">Topics & Concepts Coverage</h2>
                  <p className="text-xs text-muted">
                    Click a topic block to view its key concepts and the questions asked
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-4 gap-3">
                      {detail.topics.map((topicItem, index) => (
                        <button
                          key={index}
                          onClick={() => setOpenTopic(topicItem.topic)}
                          className="group relative flex flex-col justify-between gap-3 rounded-2xl border border-default bg-surface/40 p-4 text-left shadow-[var(--shadow)] transition hover:border-accent-soft-border hover:bg-accent-soft"
                        >
                          <span className="text-sm font-bold text-primary leading-snug line-clamp-2">
                            {topicItem.topic}
                          </span>
                          <span className="text-[11px] font-medium text-muted">
                            {topicItem.strongest_concepts.length + topicItem.weakest_concepts.length} concepts
                          </span>
                          <div>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Score</span>
                              <span className="px-1.5 py-0.5 rounded-lg text-xs font-bold bg-accent-soft text-secondary border border-accent-soft-border">
                                {parseFloat(topicItem.average_score).toFixed(1)}
                              </span>
                            </div>
                            <div className="h-1.5 w-full bg-black/30 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-btn-primary-from to-btn-primary-to"
                                style={{ width: `${parseFloat(topicItem.average_score) * 10}%` }}
                              ></div>
                            </div>
                          </div>
                          <ChevronRight className="absolute right-3 top-3 h-4 w-4 text-muted opacity-0 transition group-hover:opacity-100" />
                        </button>
                      ))}
                    </div>
            </GlassCard>
          </div>

          

        </div>

        {/* Topic Detail Modal */}
        {modalTopic && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 sm:p-6 backdrop-blur-sm"
            onClick={() => setOpenTopic(null)}
          >
            <div
              className="relative flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-default bg-card shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header — title + assessed count + single score pill */}
              <div className="flex items-center justify-between gap-4 border-b border-accent bg-surface/60 px-5 py-4 sm:px-6 shrink-0">
                <div className="flex min-w-0 items-center gap-2">
                  <h3 className="min-w-0 flex-1 text-xl font-extrabold tracking-tight text-primary truncate" title={modalTopic.topic}>
                    {modalTopic.topic}
                  </h3>
                  <span className="shrink-0 text-xs text-muted">1 interview assessed</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="inline-flex items-center rounded-lg border border-accent bg-accent px-3 py-1.5 text-xs font-bold text-white">
                    {parseFloat(modalTopic.average_score || "0").toFixed(2)} score · {parseFloat(modalTopic.confidence_score || "0").toFixed(2)} confidence
                  </span>
                  <button
                    onClick={() => setOpenTopic(null)}
                    aria-label="Close modal"
                    className="rounded-xl border border-default bg-card/60 p-2 text-secondary transition hover:border-accent-soft-border hover:bg-accent-soft shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Modal Body — single column */}
              <div className="min-h-0 flex-1 overflow-y-auto p-5 sm:px-6">
                {/* Strong Concepts */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="shrink-0 inline-flex items-center rounded-full border border-success-border bg-accent px-2.5 py-1 text-xs font-semibold text-white">
                    Strong concepts
                  </span>
                  {modalTopic.strongest_concepts.length > 0 ? (
                    modalTopic.strongest_concepts.map((concept, cIdx) => {
                        const hasLink = concept.question_ids && concept.question_ids.length > 0;
                        return (
                          <button
                            key={`${concept.concept}-${cIdx}`}
                            type="button"
                            onClick={() => handleConceptClick(concept.question_ids)}
                            disabled={!hasLink}
                            title={hasLink ? `Jump to question for "${concept.concept}"` : undefined}
                            className={`inline-flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all duration-150 ${
                              hasLink
                                ? "bg-success-soft text-success border-success-border hover:border-success/60 cursor-pointer active:scale-95"
                                : "bg-surface/50 text-muted border-default cursor-default"
                            }`}
                          >
                            {concept.concept}
                          </button>
                        );
                      })
                    ) : (
                      <span className="text-xs text-muted italic">None identified</span>
                    )}
                </div>

                {/* Weak Concepts */}
                <div className="mt-5 flex flex-wrap items-center gap-2">
                  <span className="shrink-0 inline-flex items-center rounded-full border border-danger-border bg-accent px-2.5 py-1 text-xs font-semibold text-white">
                    Weak concepts
                  </span>
                  {modalTopic.weakest_concepts.length > 0 ? (
                    modalTopic.weakest_concepts.map((concept, cIdx) => {
                        const hasLink = concept.question_ids && concept.question_ids.length > 0;
                        return (
                          <button
                            key={`${concept.concept}-${cIdx}`}
                            type="button"
                            onClick={() => handleConceptClick(concept.question_ids)}
                            disabled={!hasLink}
                            title={hasLink ? `Jump to question for "${concept.concept}"` : undefined}
                            className={`inline-flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all duration-150 ${
                              hasLink
                                ? "bg-danger-soft text-danger border-danger-border hover:border-danger/60 cursor-pointer active:scale-95"
                                : "bg-surface/50 text-muted border-default cursor-default"
                            }`}
                          >
                            {concept.concept}
                          </button>
                        );
                      })
                    ) : (
                      <span className="text-xs text-muted italic">None identified</span>
                    )}
                </div>

                <div className="my-5 border-t border-default" />

                {/* Questions */}
                {modalTopicQuestions.length > 0 && selectedQ ? (
                  <div>
                    <div className="mb-4 flex flex-wrap gap-2">
                      {modalTopicQuestions.map((q, qIdx) => {
                        const active = qIdx === selectedIdx;
                        return (
                          <button
                            key={q.id || qIdx}
                            type="button"
                            onClick={() => setSelectedQIdx(qIdx)}
                            className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition-all duration-150 ${
                              active
                                ? "border-accent-soft-border bg-accent-soft text-primary"
                                : "border-default bg-transparent text-secondary hover:border-accent-soft-border hover:text-primary"
                            }`}
                          >
                            Q{q.question_number || qIdx + 1} · {parseFloat(q.score || "0").toFixed(1)}/10
                          </button>
                        );
                      })}
                    </div>

                    <h4 className="mb-3 text-base font-bold text-primary">
                      {selectedQ.question}
                    </h4>
                    <div className="space-y-3">
                      <div className="rounded-xl border border-default bg-black/30 p-3.5">
                        <span className="mb-1.5 block text-xs text-muted">
                          Candidate answer
                        </span>
                        <p className="text-sm text-secondary leading-relaxed italic">
                          {selectedQ.answer}
                        </p>
                      </div>
                      <div className="rounded-xl border border-default bg-black/20 p-3.5">
                        <span className="mb-1.5 block text-xs text-muted">
                          AI evaluation feedback
                        </span>
                        <p className="text-sm text-primary leading-relaxed">
                          {selectedQ.feedback}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted italic">No questions recorded for this topic.</p>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}