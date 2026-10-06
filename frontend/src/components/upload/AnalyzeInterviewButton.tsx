"use client";

import { Sparkles, Loader2, UploadCloud, RotateCcw } from "lucide-react";

type AnalyzeButtonProps = {
  hasFile: boolean;
  hasExperience: boolean;
  isProcessing: boolean;
  isUploading?: boolean;
  isCompleted: boolean;
  onAnalyze: () => void;
  onReset: () => void;
};

export default function AnalyzeInterviewButton({
  hasFile,
  hasExperience,
  isProcessing,
  isUploading = false,
  isCompleted,
  onAnalyze,
  onReset,
}: AnalyzeButtonProps) {
  if (isCompleted) {
    return (
      <button
        type="button"
        onClick={onReset}
        className="group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-2xl border border-default bg-surface/60 px-6 py-4 text-sm font-bold text-secondary backdrop-blur-xl transition-all duration-200 hover:border-accent-soft-border hover:bg-accent-soft hover:text-primary focus:outline-none focus-visible:ring-4"
        style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
      >
        <RotateCcw className="h-5 w-5" />
        Analyze Another Interview
      </button>
    );
  }

  if (isProcessing) {
    return (
      <button
        type="button"
        disabled
        aria-label="Analyzing interview"
        className="relative flex w-full cursor-wait items-center justify-center gap-2.5 overflow-hidden rounded-2xl px-6 py-4 text-sm font-bold text-btn-primary-text backdrop-blur-xl transition-all duration-200"
        style={{
          background:
            "linear-gradient(to right, var(--gradient-start), var(--gradient-end))",
        }}
      >
        <Loader2 className="h-5 w-5 animate-spin" />
        {isUploading ? "Uploading your interview…" : "Analyzing your interview…"}
      </button>
    );
  }

  const ready = hasFile && hasExperience;

  return (
    <button
      type="button"
      onClick={onAnalyze}
      disabled={!ready}
      aria-label={!hasFile ? "Select a file to analyze" : !hasExperience ? "Enter years of experience to analyze" : "Analyze interview"}
      className={`group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-2xl px-6 py-4 text-sm font-bold backdrop-blur-xl transition-all duration-200 focus:outline-none focus-visible:ring-4 ${
        ready
          ? "text-btn-primary-text shadow-[0_0_25px_-3px_var(--shadow-glow)] hover:-translate-y-0.5 hover:shadow-[0_0_40px_-2px_var(--shadow-glow)] active:translate-y-0 active:scale-[0.99] cursor-pointer"
          : "cursor-not-allowed border border-default bg-black/30 text-muted"
      }`}
      style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
    >
      {/* Shimmer sweep */}
      {ready && (
        <span
          className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full"
          aria-hidden="true"
        />
      )}
      <span
        className="absolute inset-0 opacity-90"
        style={{
          background:
            "linear-gradient(to right, var(--gradient-start), var(--gradient-end))",
        }}
        aria-hidden="true"
      />
      <span className="relative z-10 flex items-center justify-center gap-2.5">
        {ready ? (
          <>
            <Sparkles className="h-5 w-5" />
            Analyze Interview
          </>
        ) : !hasFile ? (
          <>
            <UploadCloud className="h-5 w-5" />
            Select a file to analyze
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            Enter years of experience
          </>
        )}
      </span>
    </button>
  );
}
