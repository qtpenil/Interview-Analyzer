"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Stage-aware visual progress for the post-upload analysis phase.
 *
 * The backend status is the source of truth for WHICH stage we're in, but it
 * is polled only every ~4s. To keep the bar feeling alive between polls (and
 * during long stages like AI analysis) we compute a *target* percentage that
 * drifts smoothly through the current stage's safe range, then ease the
 * displayed value toward that target.
 *
 * Anti-stall / no-false-progress guarantees:
 *   - Each stage owns a [start, end) range; the visual value never exceeds
 *     `end` while that stage is active (it approaches end asymptotically).
 *   - On stage change the target jumps into the new range and the displayed
 *     value eases across — so 40% -> 60% is traversed gradually, never as a
 *     hard jump.
 *   - On completion the value is driven cleanly to 100.
 *
 * Returns a nullable value so callers can distinguish "not started" from 0.
 */

type StageRange = { start: number; end: number };

/** Per-stage safe ranges (percent). Upload handled separately. */
const STAGE_RANGES: StageRange[] = [
  { start: 0, end: 20 }, // Uploading (shown only during resume)
  { start: 20, end: 40 }, // Preparing Audio
  { start: 40, end: 60 }, // Transcribing
  { start: 60, end: 90 }, // Processing with AI (long-running)
  { start: 0, end: 0 }, // Completed -> special-cased to 100
];

/** Latest visual state, stashed outside React state. */
type SavedProgress = {
  key: string | null;
  display: number;
  target: number;
  stageStart: number;
  stageIndex: number;
};

/**
 * Module-scoped visual progress. ProcessingTracker unmounts when the user
 * navigates away, which would otherwise destroy the eased display value and
 * drift clock — returning would reseed the bar from the current stage start
 * (e.g. dropping back down to 60%) instead of resuming. Stashing the latest
 * values here lets a remount pick up exactly where it left off. Scoped per
 * interview via resetKey so a new analysis never inherits another
 * interview's progress.
 */
let savedProgress: SavedProgress | null = null;

/** Seconds to reach ~half of the way through a stage's drift window. */
const STAGE_HALF_TIME_SEC: number[] = [4, 8, 16, 90, 0];

export function useStageProgress(
  stageIndex: number,
  isCompleted: boolean,
  enabled: boolean,
  resetKey: string | null = null
): number | null {
  const safeIndex = Math.min(Math.max(stageIndex, 0), STAGE_RANGES.length - 1);

  // Track previous stage to detect large jumps (backend skipping stages)
  const prevStageRef = useRef<number>(safeIndex);
  useEffect(() => {
    const jump = safeIndex - prevStageRef.current;
    if (jump > 1 && prevStageRef.current !== 0) {
      console.warn(
        `[useStageProgress] Stage jumped from ${prevStageRef.current} to ${safeIndex} (delta ${jump}). ` +
        `Backend may be skipping intermediate stages (e.g., ANALYZING).`
      );
    }
    prevStageRef.current = safeIndex;
  }, [safeIndex]);

  // Remount restore is decided during render so the very first paint already
  // shows the resumed value (no flash of the stage start). Only applies when
  // re-mounting mid-stage for the same interview.
  const canRestore =
    enabled &&
    savedProgress !== null &&
    savedProgress.key === resetKey &&
    savedProgress.stageIndex === safeIndex;

  // Real eased display value (what the bar shows). Seeded to the CURRENT stage
  // start on first enabled render so a previously-disabled hook (during upload)
  // doesn't resume from a stale 0 and cause the bar to dip backwards at the
  // upload -> processing handoff — unless a same-stage restore applies.
  const [display, setDisplay] = useState<number>(() =>
    isCompleted
      ? 100
      : canRestore && savedProgress
        ? savedProgress.display
        : STAGE_RANGES[safeIndex]?.start ?? 0
  );
  const [target, setTarget] = useState<number>(() =>
    canRestore && savedProgress
      ? savedProgress.target
      : STAGE_RANGES[safeIndex]?.start ?? 0
  );
  const wasEnabledRef = useRef<boolean>(false);

  useEffect(() => {
    const firstActivation = enabled && !wasEnabledRef.current;
    wasEnabledRef.current = enabled;
    if (firstActivation && !canRestore) {
      const start = STAGE_RANGES[safeIndex]?.start ?? 0;
      setDisplay(isCompleted ? 100 : start);
      setTarget(start);
    }
  }, [enabled, safeIndex, isCompleted, canRestore]);

  // Drift clock. Reset ONLY on genuine stage transitions — never on mount —
  // so a remount keeps drifting from the original stage start instead of
  // restarting the stage window (which pulled the bar back down).
  const stageStartRef = useRef<number>(
    canRestore && savedProgress ? savedProgress.stageStart : 0
  );
  const clockStageRef = useRef<number>(safeIndex);
  useEffect(() => {
    if (stageStartRef.current === 0) {
      // Fresh mount with nothing to restore — start the drift clock now.
      stageStartRef.current = Date.now();
    } else if (clockStageRef.current !== safeIndex) {
      clockStageRef.current = safeIndex;
      stageStartRef.current = Date.now();
    }
  }, [safeIndex]);

  // Drive the target through the stage range as time passes.
  useEffect(() => {
    if (!enabled || isCompleted) return;
    const range = STAGE_RANGES[safeIndex];
    const half = STAGE_HALF_TIME_SEC[safeIndex] ?? 8;

    const id = setInterval(() => {
      const secs = (Date.now() - stageStartRef.current) / 1000;
      // Exponential approach: fast at the start, asymptotic toward the cap.
      const frac = half > 0 ? 1 - Math.pow(0.5, secs / half) : 1;
      setTarget(range.start + (range.end - range.start) * frac);
    }, 200);
    return () => clearInterval(id);
  }, [enabled, isCompleted, safeIndex]);

  // Ease the displayed value toward the goal (handles stage transitions and
  // the clean run to 100 on completion).
  useEffect(() => {
    if (!enabled) return;
    const goal = isCompleted ? 100 : target;
    const id = setInterval(() => {
      setDisplay((prev) => {
        const diff = goal - prev;
        if (Math.abs(diff) <= 0.2) return goal;
        // Cap the per-tick step so stage jumps 40->60 are traversed gradually.
        // When completing, use a slower max step (0.5) so the final 70->100
        // animation takes ~3s instead of ~1.4s, feeling more deliberate.
        const maxStep = isCompleted ? 0.5 : 1.1;
        const step = Math.min(maxStep, Math.max(0.3, Math.abs(diff) * 0.06));
        return prev + Math.sign(diff) * Math.min(step, Math.abs(diff));
      });
    }, 50);
    return () => clearInterval(id);
  }, [enabled, target, isCompleted]);

  // Stash the latest visual state for a future remount (navigation away and
  // back). Cheap assignment every tick; cleared on completion since the
  // completed state drives 100 on its own and must never leak into the next
  // analysis (additionally guarded by resetKey).
  useEffect(() => {
    if (!enabled) return;
    if (isCompleted) {
      savedProgress = null;
      return;
    }
    savedProgress = {
      key: resetKey,
      display,
      target,
      stageStart: stageStartRef.current,
      stageIndex: safeIndex,
    };
  }, [enabled, display, target, safeIndex, isCompleted, resetKey]);

  return enabled ? Math.max(0, Math.min(100, display)) : null;
}
