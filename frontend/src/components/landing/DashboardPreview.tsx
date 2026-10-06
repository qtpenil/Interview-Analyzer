import { Gauge, MessageSquare, Layers, TrendingUp, AlertCircle, CheckCircle2, FileDown, ShieldCheck } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import { GlassCard, StatPill, TopicBar, InsightChip, TranscriptLine } from "./MockPanels";
import { ScoreRing } from "@/components/common/ScoreRing";

const scoreItems = [
  { label: "Overall", value: "8.4" },
  { label: "Technical", value: "9.0" },
  { label: "Communication", value: "9.1" },
  { label: "Confidence", value: "7.8" },
  { label: "Knowledge", value: "8.6" },
  { label: "Alignment", value: "8.2" },
];

export default function DashboardPreview() {
  return (
    <section className="mx-auto max-w-7xl px-5 sm:px-8 py-20 sm:py-28">
      <SectionHeading
        eyebrow="Dashboard"
        title="One place for every interview"
        description="The same workspace you'll use after sign-up — scores, transcripts, topics, and reports, beautifully organized."
      />

      <Reveal className="relative mt-14">
        <div className="relative mx-auto max-w-4xl">
          <GlassCard className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-default bg-surface/40 px-5 py-3">
              <p className="text-sm font-bold text-primary">Interview Dashboard</p>
              <span className="rounded-full border border-accent-soft-border bg-accent-soft px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-secondary">
                HIRE
              </span>
            </div>

            <div className="grid gap-6 p-6 md:grid-cols-2">
              {/* Score summary */}
              <div className="flex flex-col items-center justify-center rounded-2xl border border-default bg-surface/40 p-5">
                <ScoreRing value={8.4} size={120} stroke={9} />
                <div className="mt-4 flex flex-wrap justify-center gap-1.5">
                  <InsightChip>Strong hire signal</InsightChip>
                </div>
              </div>

              {/* Score grid + topics */}
              <div className="flex flex-col gap-6 justify-center">
                <div className="grid grid-cols-3 gap-3">
                  {scoreItems.map((s) => (
                    <div
                      key={s.label}
                      className="flex flex-col items-center justify-center rounded-xl border border-default bg-surface/40 p-3 text-center"
                    >
                      <p className="text-[11px] font-medium text-muted">
                        {s.label}
                      </p>
                      <p className="mt-1 text-xl font-bold text-primary">
                        {s.value}
                        <span className="ml-0.5 text-xs font-medium text-muted">
                          /10
                        </span>
                      </p>
                    </div>
                  ))}
                </div>

                <div className="rounded-2xl border border-default bg-surface/40 p-4">
                  <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                    Topics Covered
                  </p>
                  <div className="space-y-2.5">
                    <TopicBar name="System Design" score={9} />
                    <TopicBar name="Algorithms" score={8} />
                    <TopicBar name="Behavioral" score={7} />
                  </div>
                </div>
              </div>
            </div>

            {/* Transcript strip */}
            <div className="border-t border-default bg-surface/40 p-5">
              <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                Transcript
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <TranscriptLine
                  speaker="Interviewer"
                  text="Walk me through a tricky production incident you resolved."
                />
                <TranscriptLine
                  speaker="Candidate"
                  text="We had a cascade failure; I added circuit breakers and improved observability."
                />
              </div>
            </div>
          </GlassCard>

          {/* floating cards */}
          <StatPill
            label="Communication"
            value="9.1 / 10"
            icon={<MessageSquare className="h-4 w-4" />}
            className="absolute -left-5 -top-6 hidden w-44 lg:flex animate-[float_6s_ease-in-out_infinite]"
          />
          <StatPill
            label="Strengths"
            value="12 found"
            icon={<TrendingUp className="h-4 w-4" />}
            className="absolute -right-6 top-10 hidden w-44 lg:flex animate-[float-slow_7s_ease-in-out_infinite]"
          />
          <StatPill
            label="Improve"
            value="3 areas"
            icon={<AlertCircle className="h-4 w-4" />}
            className="absolute -left-7 bottom-16 hidden w-44 lg:flex animate-[float-soft_8s_ease-in-out_infinite]"
          />
          <StatPill
            label="Report"
            value="PDF Generated"
            icon={<FileDown className="h-4 w-4" />}
            className="absolute -right-5 -bottom-6 hidden w-44 lg:flex animate-[float_9s_ease-in-out_infinite]"
          />
        </div>
      </Reveal>

      {/* secondary metric row */}
      <div className="mx-auto mt-10 grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { icon: Gauge, label: "Interview Score", value: "8.4 / 10" },
          { icon: Layers, label: "Topics Covered", value: "9" },
          { icon: CheckCircle2, label: "Questions Answered", value: "23" },
          { icon: ShieldCheck, label: "Confidence", value: "7.8 / 10" },
        ].map((m, i) => (
          <Reveal key={m.label} delay={i * 80}>
            <div className="flex flex-col items-center rounded-2xl border border-default bg-card/70 p-5 text-center backdrop-blur-xl">
              <m.icon className="h-6 w-6 text-secondary" />
              <p className="mt-3 text-lg font-bold text-primary">{m.value}</p>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                {m.label}
              </p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}