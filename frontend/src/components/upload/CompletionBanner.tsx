"use client";

import Link from "next/link";
import { CheckCircle2, FileText, Eye, RotateCcw } from "lucide-react";

type CompletionBannerProps = {
  interviewId: string | null;
  onDownload: () => void;
  onReset: () => void;
};

export default function CompletionBanner({
  interviewId,
  onDownload,
  onReset,
}: CompletionBannerProps) {
  return (
        <div className="rounded-3xl border border-default bg-card/90 p-6 backdrop-blur-xl shadow-[var(--shadow)] sm:p-8">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-accent-soft-border bg-accent-soft text-secondary shadow-[0_0_20px_-4px_var(--shadow-glow)]">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <span className="inline-block rounded-full border border-accent-soft-border bg-accent-soft px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-secondary">
                Complete
              </span>
              <h2 className="mt-1.5 text-xl font-bold text-primary sm:text-2xl">
                Interview Analysis Complete
              </h2>
              <p className="mt-1 text-sm text-secondary/60">
                Your AI assessment report is ready to review and share.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {["Analysis Complete", "Report Generated", "Score Available"].map((item) => (
              <div
                key={item}
                className="flex items-center gap-2.5 rounded-xl border border-default bg-surface/40 px-4 py-3"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
                <span className="text-sm font-medium text-secondary">{item}</span>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={onDownload}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-6 py-3 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] transition-all duration-200 hover:from-btn-primary-to hover:to-btn-primary-from hover:-translate-y-0.5 active:translate-y-0"
            >
              <FileText className="h-5 w-5" />
              Download Report
            </button>
            {interviewId && (
              <Link
                href={`/interviews/${interviewId}`}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-btn-secondary-border bg-btn-secondary-bg px-6 py-3 text-sm font-semibold text-secondary transition-all duration-200 hover:border-accent-soft-border hover:bg-accent-soft hover:text-primary"
              >
                <Eye className="h-4 w-4" />
                View Report
              </Link>
            )}
            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-btn-secondary-border bg-btn-secondary-bg px-6 py-3 text-sm font-semibold text-secondary transition-all duration-200 hover:border-accent-soft-border hover:bg-accent-soft hover:text-primary"
            >
              <RotateCcw className="h-4 w-4" />
              Analyze Another
            </button>
          </div>
        </div>
  );
}
