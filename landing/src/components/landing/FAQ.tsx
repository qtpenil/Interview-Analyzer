"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";

const faqs = [
  {
    q: "How long does analysis take?",
    a: "Most interviews are processed within a few minutes. Longer recordings or heavy traffic may take a little longer, but you'll see live progress the entire time.",
  },
  {
    q: "Can I upload large interviews?",
    a: "Yes. The platform accepts standard video and audio formats including MP4, MOV, WEBM, MP3, and WAV. Larger files are processed reliably with progress tracking.",
  },
  {
    q: "Do you store my videos?",
    a: "Uploaded media is handled with security in mind and used to generate your analysis. You stay in control of your content through your account.",
  },
  {
    q: "Can I download reports?",
    a: "Absolutely. Every analysis produces a polished, shareable PDF report you can download and send to your hiring team.",
  },
  {
    q: "How accurate is the transcription?",
    a: "Transcription is powered by modern speech models and produces structured, speaker-labeled text. Accuracy improves with clear audio and minimal background noise.",
  },
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="mx-auto max-w-3xl scroll-mt-24 px-5 sm:px-8 py-20 sm:py-28">
      <SectionHeading
        eyebrow="FAQ"
        title="Questions, answered"
        description="Everything you need to know before uploading your first interview."
      />

      <div className="mt-12 space-y-3">
        {faqs.map((faq, i) => {
          const isOpen = openIndex === i;
          return (
            <Reveal key={faq.q} delay={i * 60}>
              <div
                className={`overflow-hidden rounded-2xl border bg-card/80 backdrop-blur-xl transition-all duration-300 ${
                  isOpen
                    ? "border-accent-soft-border shadow-[var(--shadow),var(--shadow-glow)]"
                    : "border-default shadow-[var(--shadow),var(--shadow-glow)] hover:border-accent-soft-border"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                  aria-expanded={isOpen}
                  aria-controls={`faq-panel-${i}`}
                >
                  <span className="text-base font-semibold text-primary">
                    {faq.q}
                  </span>
                  <ChevronDown
                    className={`h-5 w-5 shrink-0 text-secondary transition-transform duration-300 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>
                <div
                  id={`faq-panel-${i}`}
                  className={`grid transition-all duration-300 ease-out ${
                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  }`}
                >
                  <div className="overflow-hidden">
                    <p className="px-5 pb-5 text-sm leading-7 text-secondary">
                      {faq.a}
                    </p>
                  </div>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
