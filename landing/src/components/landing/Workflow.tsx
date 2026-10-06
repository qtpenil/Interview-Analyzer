import { UploadCloud, AudioLines, BrainCircuit, ClipboardCheck, FileDown, Eye } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import DemoVideo from "./DemoVideo";

const steps = [
  {
    icon: UploadCloud,
    title: "Upload Interview",
    text: "Drop in your video or audio recording. We accept MP4, MOV, WEBM, MP3 and WAV.",
  },
  {
    icon: AudioLines,
    title: "AI Transcribes",
    text: "Speech is converted into a structured transcript with clear speaker labels.",
  },
  {
    icon: BrainCircuit,
    title: "AI Understands Conversation",
    text: "The model maps questions, answers, and the topics discussed throughout.",
  },
  {
    icon: ClipboardCheck,
    title: "Evaluates Every Answer",
    text: "Each response is scored on clarity, relevance, confidence, and completeness.",
  },
  {
    icon: FileDown,
    title: "Generates Report",
    text: "A professional, downloadable PDF is produced with scores and recommendations.",
  },
  {
    icon: Eye,
    title: "Review Insights",
    text: "Open the dashboard to explore insights, share feedback, and make decisions.",
  },
];

export default function Workflow() {
  return (
    <section
      id="workflow"
      className="relative scroll-mt-24 border-y border-default bg-surface/40 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <SectionHeading
          eyebrow="Workflow"
          title="From recording to report in six steps"
          description="A guided pipeline that turns a single interview into structured, decision-ready intelligence."
        />

        <Reveal delay={80} className="mx-auto mt-12 max-w-4xl">
          <DemoVideo />
        </Reveal>

        <div className="relative mt-16">
          {/* vertical connector */}
          <div className="absolute left-8 top-4 bottom-4 w-px bg-gradient-to-b from-btn-primary-from/40 via-accent-soft to-transparent md:left-1/2 md:-translate-x-1/2" />

          <ol className="space-y-10 md:space-y-12">
            {steps.map((step, i) => {
              const isLeft = i % 2 === 0;
              return (
                <Reveal
                  key={step.title}
                  delay={i * 70}
                  as="li"
                  className="relative md:grid md:grid-cols-2 md:gap-12"
                >
                  {/* node */}
                  <span className="absolute left-8 top-0 z-10 flex h-9 w-9 -translate-x-1/2 items-center justify-center rounded-full border border-accent-soft-border bg-card text-secondary shadow-[0_0_18px_-4px_var(--shadow-glow)] md:left-1/2">
                    <step.icon className="h-4 w-4" />
                  </span>

                  <div
                    className={
                      isLeft
                        ? "ml-16 md:ml-0 md:pr-16 md:text-right md:col-start-1 md:row-start-1"
                        : "ml-16 md:ml-0 md:col-start-2 md:row-start-1 md:pl-4"
                    }
                  >
                    <div className="rounded-2xl border border-default bg-card/80 p-5 backdrop-blur-xl shadow-[var(--shadow)] transition-all duration-300 hover:border-accent-soft-border hover:-translate-y-1">
                      <span className="text-xs font-bold uppercase tracking-widest text-accent">
                        Step {i + 1}
                      </span>
                      <h3 className="mt-1.5 text-lg font-bold text-primary">
                        {step.title}
                      </h3>
                      <p className="mt-2 text-sm leading-6 text-secondary">
                        {step.text}
                      </p>
                    </div>
                  </div>
                </Reveal>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}
