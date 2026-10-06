"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import Reveal from "./Reveal";
import Button from "./Button";

export default function CTA() {
  return (
    <section className="mx-auto max-w-7xl px-5 sm:px-8 py-20 sm:py-28">
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl border border-default bg-gradient-to-br from-btn-primary-from/10 via-card/90 to-btn-primary-to/10 px-6 py-16 text-center sm:px-12 sm:py-20 shadow-[var(--shadow),0_24px_60px_-24px_var(--shadow-glow)]">
          <div className="pointer-events-none absolute inset-0 bg-[var(--gradient-radial)]" />
          <div className="pointer-events-none absolute -bottom-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full blur-[110px] opacity-20" style={{ background: "var(--gradient-start)" }} />

          <div className="relative mx-auto max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-accent-soft-border bg-accent-soft px-3 py-1 text-xs font-bold uppercase tracking-widest text-secondary">
              <Sparkles className="h-3.5 w-3.5" />
              Get started today
            </span>
            <h2 className="mt-6 text-3xl font-extrabold tracking-tight text-primary sm:text-5xl">
              Ready to improve every interview?
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-secondary">
              Join teams turning raw recordings into fair, fast, and evidence-based
              hiring decisions. Create your free account in under a minute.
            </p>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button href="/register" variant="primary" size="lg">
                Sign Up Free
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button href="#features" variant="secondary" size="lg">
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
