import { AlertTriangle, ArrowRight } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import Button from "./Button";

const problems = [
  {
    title: "Mistakes go unnoticed",
    text: "Candidates and interviewers rarely get objective feedback on what actually went wrong.",
  },
  {
    title: "Interviews are never reviewed",
    text: "Valuable recordings sit untouched because rewatching 45 minutes is slow and tedious.",
  },
  {
    title: "Feedback is subjective",
    text: "Notes depend on who's in the room, leading to inconsistent and biased evaluations.",
  },
  {
    title: "No structured insights",
    text: "Raw conversation holds the answers, but there's no easy way to extract them.",
  },
];

export default function Problem() {
  return (
    <section className="mx-auto max-w-7xl px-5 sm:px-8 py-20 sm:py-28">
      <SectionHeading
        eyebrow="The Problem"
        title="Interview preparation is hard."
        description="Great candidates are lost and great hires are missed because interviews are opaque, manual, and impossible to review at scale."
      />

      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {problems.map((item, i) => (
          <Reveal key={item.title} delay={i * 90}>
            <div className="h-full rounded-3xl border border-default bg-card/60 p-6 backdrop-blur-xl shadow-[var(--shadow)] transition-all duration-300 hover:border-accent-soft-border hover:-translate-y-1">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-warning-soft text-warning border border-warning-border">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-primary">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-secondary">
                {item.text}
              </p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal className="mt-14" delay={120}>
        <div className="relative overflow-hidden rounded-3xl border border-default bg-gradient-to-br from-btn-primary-from/10 via-card/90 to-btn-primary-to/10 p-8 sm:p-12 text-center shadow-[var(--shadow)]">
          <div className="absolute inset-0 bg-[var(--gradient-radial)]" />
          <div className="relative">
            <h3 className="text-2xl font-extrabold tracking-tight text-primary sm:text-3xl">
              Our platform solves this.
            </h3>
            <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-secondary">
              Every recording becomes a structured, scored, and shareable
              assessment — so decisions are fair, fast, and based on evidence.
            </p>
            <div className="mt-7 flex justify-center">
              <Button href="#features" variant="primary" size="lg">
                See how it works
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
