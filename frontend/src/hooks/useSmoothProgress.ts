"use client";

import { useEffect, useState } from "react";

/**
 * Eases a numeric target toward its value in small increments instead of
 * jumping, so progress bars climb smoothly (e.g. 43 → 44 → 45… → 57).
 *
 * Returns `null` while the target is `null`; when a target first arrives the
 * display starts from that value and then trails it with an ease-out step,
 * producing steady ~1% ticks rather than chunky network-driven jumps.
 */
export function useSmoothedValue(
  target: number | null,
  options?: { stepMs?: number }
): number | null {
  const stepMs = options?.stepMs ?? 50;
  const [display, setDisplay] = useState<number | null>(target);

  useEffect(() => {
    if (target === null) {
      setDisplay(null);
      return;
    }

    // First sighting of a target: adopt it immediately (no reverse animation
    // from a stale lower value on remount), then trail subsequent targets.
    let started = false;
    setDisplay((prev) => {
      if (prev === null) {
        started = true;
        return target;
      }
      return prev;
    });

    const id = setInterval(() => {
      setDisplay((prev) => {
        if (prev === null) return started ? prev : target;
        const diff = target - prev;
        // Snap when close enough so we always land exactly on the target.
        if (Math.abs(diff) <= 0.5) return target;
        const step = Math.max(0.35, Math.abs(diff) * 0.12);
        return prev + Math.sign(diff) * Math.min(step, Math.abs(diff));
      });
    }, stepMs);

    return () => clearInterval(id);
  }, [target, stepMs]);

  return display;
}
