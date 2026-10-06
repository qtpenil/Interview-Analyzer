import { Zap, Target, MousePointerClick, Palette, FileText, Smartphone, Lock, Boxes } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import { GlassCard } from "./MockPanels";

const reasons = [
  { icon: Zap, title: "Fast Processing", text: "Most interviews are analyzed in minutes, not hours." },
  { icon: Target, title: "Accurate AI", text: "Transcripts and scores grounded in the actual conversation." },
  { icon: MousePointerClick, title: "Easy to Use", text: "Upload, wait, and review — no setup or training needed." },
  { icon: Palette, title: "Beautiful Dashboard", text: "Insights presented clearly, not buried in spreadsheets." },
  { icon: FileText, title: "Professional Reports", text: "Share-ready PDFs your hiring team will actually read." },
  { icon: Smartphone, title: "Modern Interface", text: "A clean, responsive experience on every device." },
  { icon: Lock, title: "Secure Uploads", text: "Candidate media is processed with security in mind." },
  { icon: Boxes, title: "Scalable Architecture", text: "Built to handle a single role or thousands of interviews." },
];

export default function WhyChooseUs() {
  return (
    <section className="mx-auto max-w-7xl px-5 sm:px-8 py-20 sm:py-28">
      <SectionHeading
        eyebrow="Why us"
        title="Why teams choose this platform"
        description="Purpose-built for interview analysis — fast, accurate, and a joy to use."
      />

      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {reasons.map((reason, i) => (
          <Reveal key={reason.title} delay={(i % 4) * 70}>
            <GlassCard className="group h-full p-6 transition-all duration-300 hover:-translate-y-1 hover:border-accent-soft-border">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-secondary border border-accent-soft-border transition-transform duration-300 group-hover:scale-105">
                <reason.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-base font-bold text-primary">{reason.title}</h3>
              <p className="mt-1.5 text-sm leading-6 text-secondary">
                {reason.text}
              </p>
            </GlassCard>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
