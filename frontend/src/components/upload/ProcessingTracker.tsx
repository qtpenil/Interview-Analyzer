"use client";

import { useMemo } from "react";
import {
  Loader2,
  AlertCircle,
  Check,
  XCircle,
  Circle,
} from "lucide-react";
import { useUpload } from "@/context/UploadContext";
import { Progress } from "@/components/ui/Progress";
import { useSmoothedValue } from "@/hooks/useSmoothProgress";
import { useStageProgress } from "@/hooks/useStageProgress";
import { useTypedStatus } from "@/hooks/useTypedStatus";
import { cn } from "@/lib/utils";

// The five visible stages of the processing timeline. Keep this array as the
// single source of the stage labels — getStageIndex and the timeline both
// derive from it.
const STAGES = [
  "Uploading",
  "Preparing Audio",
  "Transcribing",
  "Processing with AI",
  "Completed",
];

function getStageIndex(status: string): number {
  const s = status.toLowerCase();
  if (s.includes("report ready") || s.includes("✅")) return 4;
  if (s.includes("analyz") || s.includes("insight") || s.includes("pdf") || s.includes("creating")) return 3;
  if (s.includes("transcrib")) return 2;
  if (s.includes("audio") || s.includes("starting processing") || s.includes("uploaded") || s.includes("resum"))
    return 1;
  if (s.includes("upload")) return 0;
  return 0;
}

// Message source of truth — which detail lines each status phase can show.
// The active stage picks its messages here and feeds them to the typing hook.
const STATUS_DETAILS: Array<{ match: RegExp; lines: string[] }> = [
  {
    match: /report ready|✅/,
    lines: ["All done — your report is ready to download."],
  },
  {
    match: /analyz|insight|pdf|creating/,
    lines: [
      "Analyzing interview responses with AI…",
      "Scoring communication, confidence, and depth…",
      "Comparing responses against the role rubric…",
      "Generating personalized insights and feedback…",
      "Preparing your polished PDF report…",
    ],
  },
  {
    match: /transcrib/,
    lines: [
      "Converting speech to text with AI transcription…",
      "Labeling speakers — interviewer vs. candidate…",
      "Aligning every answer to its question…",
    ],
  },
  {
    match: /audio|processing/,
    lines: [
      "Converting your recording to a clean WAV track…",
      "Cleansing audio — removing noise, leveling volume…",
      "Detecting speech segments and question boundaries…",
    ],
  },
  {
    match: /upload/,
    lines: [
      "Uploading your interview…",
      "Securely transferring your recording to the server…",
    ],
  },
  {
    match: /starting processing|uploaded/,
    lines: ["Queued on the server — preparing your file for the pipeline…"],
  },
  {
    match: /cancelling|cancel/,
    lines: ["Stopping the pipeline and cleaning up resources…"],
  },
  {
    match: /resum/,
    lines: ["Reconnecting to your in-flight analysis…"],
  },
];

function getStatusDetails(status: string): string[] {
  for (const entry of STATUS_DETAILS) {
    if (entry.match.test(status.toLowerCase())) return entry.lines;
  }
  return ["Working on your interview…"];
}

/* Small timeline node shared by desktop (horizontal) and mobile (vertical). */
function StageIndicator({
  index,
  i,
  completed,
}: {
  index: number;
  i: number;
  completed: boolean;
}) {
  const done = completed || i < index;
  const active = !completed && i === index;

  if (done) {
    return (
      <span
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-success text-inverse shadow-[0_0_14px_-3px_var(--success)]"
        aria-hidden="true"
      >
        <Check className="h-4 w-4" strokeWidth={3} />
      </span>
    );
  }

  if (active) {
    return (
      <span className="relative flex h-7 w-7 shrink-0 items-center justify-center" role="status" aria-live="polite">
        <span className="tracker-pulse-ring absolute inset-0 rounded-full border border-secondary/70" />
        <span className="tracker-breathe flex h-7 w-7 items-center justify-center rounded-full border border-secondary bg-surface-hover">
          <span className="h-2 w-2 rounded-full bg-secondary" />
        </span>
      </span>
    );
  }

  return (
    <span
      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-default bg-black/30"
      aria-hidden="true"
    >
      <Circle className="h-3 w-3 text-muted" strokeWidth={1.5} />
    </span>
  );
}

function StageTimeline({ index, completed }: { index: number; completed: boolean }) {
  return (
    <>
      {/* Desktop / tablet — horizontal stepper */}
      <ol className="hidden w-full items-start sm:flex" aria-label="Processing stages">
        {STAGES.map((label, i) => (
          <li key={label} className="flex flex-1 flex-col items-stretch">
            <div className="flex items-center">
              <span
                className={cn(
                  "h-0.5 flex-1 rounded-full transition-colors duration-500",
                  (completed || index >= i) && i > 0
                    ? "bg-gradient-to-r from-[var(--btn-primary-from)] to-[var(--btn-primary-to)]"
                    : "bg-muted/30"
                )}
                aria-hidden="true"
              />
              <StageIndicator index={index} i={i} completed={completed} />
              <span
                className={cn(
                  "h-0.5 flex-1 rounded-full transition-colors duration-500",
                  i < STAGES.length - 1 && (completed || index > i)
                    ? "bg-gradient-to-r from-[var(--btn-primary-from)] to-[var(--btn-primary-to)]"
                    : "bg-muted/30"
                )}
                aria-hidden="true"
              />
            </div>
            <span
              className={cn(
                "mt-2 text-center text-[11px] leading-tight",
                completed || i < index
                  ? "font-semibold text-secondary"
                  : i === index
                  ? "font-bold text-primary"
                  : "text-muted"
              )}
            >
              {label}
            </span>
          </li>
        ))}
      </ol>

      {/* Mobile — vertical stepper */}
      <ol className="w-full space-y-1 sm:hidden" aria-label="Processing stages">
        {STAGES.map((label, i) => {
          const done = completed || i < index;
          const active = !completed && i === index;
          return (
            <li key={label} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                <StageIndicator index={index} i={i} completed={completed} />
                {i < STAGES.length - 1 && (
                  <span
                    className={cn(
                      "mt-1 w-0.5 flex-1 rounded-full",
                      (completed || index > i) ? "bg-secondary/70" : "bg-muted/30"
                    )}
                    aria-hidden="true"
                  />
                )}
              </div>
              <span
                className={cn(
                  "pb-3 text-[13px] leading-relaxed",
                  done
                    ? "font-semibold text-secondary"
                    : active
                    ? "font-bold text-primary"
                    : "text-muted"
                )}
              >
                {label}
              </span>
            </li>
          );
        })}
      </ol>
    </>
  );
}

export default function ProcessingTracker() {
  const {
    isProcessing,
    isLoading,
    status,
    error,
    isCompleted,
    isCancelling,
    handleCancel,
    uploadProgress,
    selectedFile,
    interviewId,
    phase,
  } = useUpload();

  const isUploading = phase === "uploading";

  // Upload uses real byte-based progress, eased so bursts become smooth ticks.
  const smoothedUpload = useSmoothedValue(uploadProgress);
  const uploadPct = smoothedUpload === null ? null : Math.round(smoothedUpload);

  const stageIndex = getStageIndex(status);
  const timelineIndex = isUploading ? 0 : stageIndex;

  // -------------------------------------------------------------------------
  // MONOTONIC COMBINED PROGRESS.
  //
  // Both "upload" and "processing" feed the SAME progress bar, but they use
  // different scales. If the upload bar showed its real 0-100 then processing
  // started from its own stage-1 value (~20), the bar would visibly jump
  // backwards (100 -> 20). To keep it monotonic, the bar is a single combined
  // 0-100 "overall" scale that matches the 5-stage timeline:
  //   Uploading 0-20 | Preparing 20-40 | Transcribing 40-60 | AI 60-90 | Done.
  //
  // Byte upload (0-100) is mapped onto the first stage range (0 -> 20); the
  // anti-stall useStageProgress already reports on this same combined scale.
  // At the upload->processing handoff the value is continuous at ~20, so the
  // bar never resets backwards.
  // -------------------------------------------------------------------------
  const FIRST_STAGE_END = 20; // end of the "Uploading" stage

  const analysisProgress = useStageProgress(
    stageIndex,
    isCompleted,
    phase === "processing" || phase === "completed",
    // Scope the remount-resume cache to this interview so a new analysis
    // never inherits the previous interview's visual progress.
    interviewId
  );

  // Phase-selected single value: upload (mapped onto the first stage range so
  // the handoff is continuous at ~20) or stage-aware analysis progress. Fed
  // directly to the bar — each source already eases internally, so no extra
  // smoothing layer here (which previously froze the value at 0).
  const progress =
    phase === "uploading"
      ? Math.round(((uploadPct ?? 0) / 100) * FIRST_STAGE_END)
      : Math.round(analysisProgress ?? 0);

  // Message source of truth — stable per status so the typing hook resets only
  // on genuine stage changes.
  const details = useMemo(() => getStatusDetails(status), [status]);

  const { text: typedText, messageId } = useTypedStatus(
    details,
    isProcessing && !error,
    32,
    2000
  );

  // Ensure an upload-only / processing-only guard.
  if (!isProcessing && !isLoading && !isCompleted) return null;

  const cancelButton = (
    <button
      type="button"
      onClick={handleCancel}
      disabled={isCancelling}
      className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-danger-border bg-danger-soft px-4 py-2.5 text-sm font-semibold text-danger transition-all duration-200 hover:bg-danger/20 active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
    >
      {isCancelling ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <XCircle className="h-4 w-4" />
      )}
      {isCancelling ? "Cancelling..." : isUploading ? "Cancel Upload" : "Cancel Analysis"}
    </button>
  );

  const totalMB = selectedFile
    ? (selectedFile.size / (1024 * 1024)).toFixed(1)
    : null;
  const uploadedMB =
    selectedFile && smoothedUpload !== null
      ? ((smoothedUpload / 100) * selectedFile.size / (1024 * 1024)).toFixed(1)
      : null;

  return (
    <div className="overflow-hidden rounded-3xl border border-default bg-card/90 p-6 backdrop-blur-xl shadow-[var(--shadow)] sm:p-7">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-bold text-primary">
          {isUploading ? (
            <Loader2 className="h-4 w-4 animate-spin text-secondary" />
          ) : (
            <span
              className={cn(
                "flex h-4 w-4 items-center justify-center rounded-full",
                isCompleted ? "bg-success text-inverse" : "tracker-breathe bg-secondary"
              )}
            >
              {isCompleted ? (
                <Check className="h-2.5 w-2.5" strokeWidth={3} />
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-background" />
              )}
            </span>
          )}
          {isCompleted
            ? "Analysis Complete"
            : isUploading
            ? "Uploading Your Interview"
            : "Analyzing Your Interview"}
        </h3>
        <span className="text-2xl font-extrabold tabular-nums tracking-tight text-primary">
          {progress}
          <span className="text-base font-semibold text-muted">%</span>
        </span>
      </div>

      {/* Typed status message */}
      <div className="mb-4 flex min-h-[1.5rem] items-center gap-2">
        <p
          key={messageId}
          className="tracker-message-in text-[13px] font-medium leading-snug text-secondary"
          aria-live="polite"
        >
          {typedText}
          {isProcessing && !isCompleted && (
            <span className="tracker-caret ml-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 rounded-full bg-secondary" />
          )}
        </p>
        {isUploading && uploadedMB && totalMB && (
          <span className="ml-auto shrink-0 text-[11px] tabular-nums text-muted">
            {uploadedMB} / {totalMB} MB
          </span>
        )}
      </div>

      {/* Progress bar */}
      <Progress
        value={progress}
        shimmer={isProcessing && !error && !isCompleted}
        aria-label={isUploading ? "Upload progress" : "Analysis progress"}
        aria-busy={isProcessing}
      />

      {/* Stage timeline */}
      <div className="mt-6">
        <StageTimeline
          index={timelineIndex}
          completed={isCompleted || stageIndex >= STAGES.length - 1}
        />
      </div>

      {/* Error state — stop all "working" animations */}
      {error && !isProcessing && (
        <div
          role="alert"
          className="mt-5 flex items-center gap-2.5 rounded-xl border border-danger-border bg-danger-soft px-4 py-3 text-sm text-danger"
        >
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            <span className="font-semibold">Something went wrong:</span> {error}
          </span>
        </div>
      )}

      {/* Error state — stop all "working" animations */}
      {error && !isProcessing && (
        <div
          role="alert"
          className="mt-5 flex items-center gap-2.5 rounded-xl border border-danger-border bg-danger-soft px-4 py-3 text-sm text-danger"
        >
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            <span className="font-semibold">Something went wrong:</span> {error}
          </span>
        </div>
      )}

      {isProcessing && !error && cancelButton}
    </div>
  );
}
