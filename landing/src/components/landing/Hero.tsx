"use client";

import { ArrowRight, Play, Sparkles, FileText, Gauge, MessageSquare } from "lucide-react";
import Button from "./Button";
import Reveal from "./Reveal";
import { GlassCard, StatPill, InsightChip, TopicBar, TranscriptLine } from "./MockPanels";
import { ScoreRing } from "@/components/common/ScoreRing";

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 py-16 md:py-24 lg:grid-cols-2 lg:gap-10">
        {/* Left — copy */}
        <div className="max-w-xl">
          <Reveal>
            <span className="inline-flex items-center gap-2 rounded-full border border-accent-soft-border bg-accent-soft px-3 py-1 text-xs font-bold uppercase tracking-widest text-secondary">
              <Sparkles className="h-3.5 w-3.5" />
              AI-Powered Interview Intelligence
            </span>
          </Reveal>

          <Reveal delay={80}>
            <h1 className="mt-6 text-4xl font-extrabold leading-[1.08] tracking-tight text-primary sm:text-5xl lg:text-6xl">
              Turn Every Interview Into{" "}
              <span className="bg-gradient-to-r from-btn-primary-from to-btn-primary-to bg-clip-text text-transparent">
                Actionable Insights
              </span>
            </h1>
          </Reveal>

          <Reveal delay={160}>
            <p className="mt-6 text-base leading-7 text-secondary sm:text-lg">
              Upload your interview recording and receive AI-powered transcripts,
              question analysis, communication insights, topic breakdowns, and a
              professionally generated report — all within minutes.
            </p>
          </Reveal>

          <Reveal delay={240}>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button href="/register" variant="primary" size="lg">
                Start Free
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button href="#workflow" variant="secondary" size="lg">
                <Play className="h-4 w-4" />
                View Demo
              </Button>
            </div>
          </Reveal>

          <Reveal delay={320}>
            <p className="mt-5 text-xs text-muted">
              No credit card required · Free tier includes 3 interviews / month
            </p>
          </Reveal>
        </div>

        {/* Right — dashboard mock */}
        <Reveal delay={200} className="relative">
          <div className="relative mx-auto max-w-lg">
            <GlassCard className="overflow-hidden">
              {/* window chrome */}
              <div className="flex items-center gap-2 border-b border-default bg-surface/40 px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-danger/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-warning/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/60" />
                <span className="ml-3 text-[11px] font-medium text-muted">
                  interview-ai.app / analysis
                </span>
                <span className="ml-auto rounded-full border border-accent-soft-border bg-accent-soft px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-secondary">
                  Complete
                </span>
              </div>

              <div className="space-y-5 p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-bold text-primary">
                      Senior Backend Engineer
                    </p>
                    <p className="text-[11px] text-muted">
                      Duration 42:18 · 23 questions
                    </p>
                  </div>
                  <ScoreRing value={8.4} size={84} stroke={7} />
                </div>

                <div className="space-y-3 rounded-2xl border border-default bg-surface/40 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-secondary">
                    Transcript
                  </p>
                  <TranscriptLine
                    speaker="Interviewer"
                    text="How would you design a rate limiter for a public API?"
                  />
                  <TranscriptLine
                    speaker="Candidate"
                    text="I'd use a token bucket with Redis, then add sliding-window fallback for bursts."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-2xl border border-default bg-surface/40 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-secondary mb-3">
                      Topics
                    </p>
                    <div className="space-y-2.5">
                      <TopicBar name="System Design" score={9} />
                      <TopicBar name="Communication" score={8} />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-default bg-surface/40 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-secondary mb-3">
                      AI Insights
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      <InsightChip>Clear structure</InsightChip>
                      <InsightChip>Confident</InsightChip>
                      <InsightChip>Deep knowledge</InsightChip>
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* floating stat cards */}
            <StatPill
              label="Communication"
              value="9.1 / 10"
              icon={<MessageSquare className="h-4 w-4" />}
              className="absolute -left-6 -top-6 hidden sm:flex animate-[float_6s_ease-in-out_infinite]"
            />
            <StatPill
              label="Report"
              value="PDF Ready"
              icon={<FileText className="h-4 w-4" />}
              className="absolute -right-5 top-1/3 hidden sm:flex animate-[float-slow_7s_ease-in-out_infinite]"
            />
            <StatPill
              label="Confidence"
              value="7.8 / 10"
              icon={<Gauge className="h-4 w-4" />}
              className="absolute -bottom-6 right-4 hidden sm:flex animate-[float-soft_8s_ease-in-out_infinite]"
            />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
