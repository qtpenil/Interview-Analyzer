import {
  AudioLines,
  HelpCircle,
  BrainCircuit,
  Layers,
  ScrollText,
  FileDown,
  UploadCloud,
  LayoutDashboard,
  ShieldCheck,
} from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import { GlassCard } from "./MockPanels";

const features = [
  {
    icon: AudioLines,
    title: "AI Speech Transcription",
    text: "Automatically converts interview recordings into clean, structured conversations with speaker labels.",
  },
  {
    icon: HelpCircle,
    title: "Question Detection",
    text: "Detects interviewer questions and candidate answers, mapping the natural flow of the discussion.",
  },
  {
    icon: BrainCircuit,
    title: "AI Assessment",
    text: "Evaluates every response for quality, clarity, relevance, confidence, and completeness.",
  },
  {
    icon: Layers,
    title: "Topic Analysis",
    text: "Groups the interview into major discussion topics and scores coverage for each area.",
  },
  {
    icon: ScrollText,
    title: "Interview Summary",
    text: "Automatically generates concise, readable summaries of the entire conversation.",
  },
  {
    icon: FileDown,
    title: "Professional Reports",
    text: "Generate polished, downloadable PDF reports you can share with hiring teams.",
  },
  {
    icon: UploadCloud,
    title: "Video Upload",
    text: "Upload interview recordings in seconds with drag-and-drop for video or audio.",
  },
  {
    icon: LayoutDashboard,
    title: "Central Dashboard",
    text: "Access every interview, score, and report from one organized, searchable place.",
  },
  {
    icon: ShieldCheck,
    title: "Modern Authentication",
    text: "Secure login and account management keep candidate data protected at all times.",
  },
];

export default function Features() {
  return (
    <section id="features" className="mx-auto max-w-7xl scroll-mt-24 px-5 sm:px-8 py-20 sm:py-28">
      <SectionHeading
        eyebrow="Features"
        title="Everything you need to analyze an interview"
        description="A complete pipeline — from raw recording to a professional, scored report — built on the same dashboard you'll use every day."
      />

      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, i) => (
          <Reveal key={feature.title} delay={(i % 3) * 90}>
            <GlassCard className="group h-full p-6 transition-all duration-300 hover:-translate-y-1 hover:border-accent-soft-border hover:shadow-[0_0_0_1px_var(--accent-soft-border),0_24px_70px_-15px_rgba(0,0,0,0.9),0_0_60px_-8px_var(--shadow-glow)]">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)] transition-transform duration-300 group-hover:scale-105">
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-primary">{feature.title}</h3>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {feature.text}
              </p>
            </GlassCard>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
