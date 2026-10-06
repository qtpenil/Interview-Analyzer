import {
  ScrollText,
  Layers,
  HelpCircle,
  BrainCircuit,
  MessageSquare,
  Gauge,
  Lightbulb,
  FileDown,
} from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import { GlassCard, TopicBar, InsightChip } from "./MockPanels";

const reportCards = [
  { icon: ScrollText, title: "Summary", text: "A concise overview of the candidate's performance and key takeaways." },
  { icon: Layers, title: "Topics", text: "Every discussion area with coverage scores and depth of understanding." },
  { icon: HelpCircle, title: "Questions", text: "The full list of questions asked, with how each was answered." },
  { icon: BrainCircuit, title: "AI Feedback", text: "Targeted, objective feedback on strengths and gaps per response." },
  { icon: MessageSquare, title: "Communication Analysis", text: "Clarity, structure, and confidence measured from the conversation." },
  { icon: Gauge, title: "Scores", text: "Multi-dimensional scores across technical, behavioral, and soft skills." },
  { icon: Lightbulb, title: "Recommendations", text: "Clear next steps and what to probe in a follow-up discussion." },
  { icon: FileDown, title: "Report Download", text: "Export a polished PDF to share with your hiring team instantly." },
];

export default function Reports() {
  return (
    <section
      id="reports"
      className="relative scroll-mt-24 border-y border-default bg-surface/40 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <SectionHeading
          eyebrow="Reports"
          title="A report that actually drives decisions"
          description="Each analysis compiles into a structured document your whole team can read in minutes."
        />

        <div className="mt-14 grid items-center gap-12 lg:grid-cols-2">
          {/* feature grid */}
          <div className="grid gap-4 sm:grid-cols-2">
            {reportCards.map((card, i) => (
              <Reveal key={card.title} delay={(i % 4) * 70}>
                <GlassCard className="group h-full p-5 transition-all duration-300 hover:-translate-y-1 hover:border-accent-soft-border">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-secondary border border-accent-soft-border transition-transform duration-300 group-hover:scale-105">
                    <card.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 text-base font-bold text-primary">{card.title}</h3>
                  <p className="mt-1.5 text-sm leading-6 text-secondary">
                    {card.text}
                  </p>
                </GlassCard>
              </Reveal>
            ))}
          </div>

          {/* report preview */}
          <Reveal delay={120}>
          <GlassCard className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-default bg-surface/40 px-5 py-3">
              <p className="text-sm font-bold text-primary">Assessment Report.pdf</p>
              <span className="rounded-full border border-accent-soft-border bg-accent-soft px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-secondary">
                Preview
              </span>
            </div>
            <div className="space-y-5 p-6">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Candidate
                </p>
                <p className="mt-1 text-lg font-bold text-primary">
                  Alex Morgan · Senior Backend Engineer
                </p>
              </div>

              <div className="rounded-2xl border border-default bg-surface/40 p-4">
                <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Topic Scores
                </p>
                <div className="space-y-2.5">
                  <TopicBar name="System Design" score={9} />
                  <TopicBar name="Algorithms" score={8} />
                  <TopicBar name="Behavioral" score={7} />
                </div>
              </div>

              <div>
                <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  AI Feedback
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <InsightChip>Strong system design</InsightChip>
                  <InsightChip>Clear communicator</InsightChip>
                  <InsightChip>Watch: concurrency depth</InsightChip>
                </div>
              </div>

              <button
                type="button"
                className="w-full rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-5 py-3 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] transition-all duration-200 hover:from-btn-primary-to hover:to-btn-primary-from"
              >
                Download Full PDF Report
              </button>
            </div>
          </GlassCard>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
