"use client";

import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Types out a rotating set of status messages with a subtle "typing" effect,
 * then pauses before advancing to the next message. Used beneath the progress
 * bar so the app feels alive while a stage is running.
 *
 * - The provided `messages` array is treated as a stable stage — whenever the
 *   stage changes (a new messages array), the cycle instantly resets to the
 *   first message and the caret starts fresh. No stale message from the
 *   previous stage ever leaks into the new stage.
 * - Respects `prefers-reduced-motion`: when the user requests reduced motion,
 *   the full first message is shown immediately (no per-char typing).
 *
 * Returns:
 *   text      - the portion of the current message to display
 *   messageId - the index of the current message, for a fade-in keyed to the
 *               newly-typed message.
 */
export function useTypedStatus(
  messages: string[],
  active: boolean,
  typeMsPerChar = 35,
  holdMs = 2000
): { text: string; messageId: number } {
  const key = useMemo(() => messages.join("\u0000"), [messages]);
  const [msgIdx, setMsgIdx] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const reducedRef = useRef(false);
  const keyRef = useRef(key);

  // Read the reduced-motion preference once (client-only).
  useEffect(() => {
    reducedRef.current =
      typeof window !== "undefined" &&
      !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  }, []);

  const msg = messages[Math.min(msgIdx, messages.length - 1)] ?? "";
  const msgLen = msg.length;

  // Drive the typing / hold / advance state machine. All state updates happen
  // inside the async timer callback (never synchronously in the effect body).
  // The effect re-runs whenever msgIdx/charCount change, so it always knows
  // how long to wait before the next transition.
  useEffect(() => {
    if (!active || messages.length === 0) return;
    let disposed = false;

    const keyChanged = keyRef.current !== key;
    keyRef.current = key;

    const reduced = reducedRef.current;

    // Determine how long to wait and what to do on the next tick.
    let delay: number;
    if (keyChanged) {
      delay = 0; // reset cycle to the new stage immediately
    } else if (reduced) {
      delay = charCount < msgLen ? 0 : holdMs;
    } else if (charCount < msgLen) {
      delay = typeMsPerChar;
    } else {
      delay = holdMs;
    }

    const timer = setTimeout(() => {
      if (disposed) return;

      if (keyChanged) {
        setMsgIdx(0);
        setCharCount(0);
        return;
      }

      if (reduced) {
        // Reveal the whole message, then rotate on the hold timer.
        if (charCount < msgLen) {
          setCharCount(msgLen);
        } else {
          setMsgIdx((i) => (i + 1) % messages.length);
          setCharCount(0);
        }
        return;
      }

      if (charCount < msgLen) {
        setCharCount((c) => c + 1);
      } else {
        setMsgIdx((i) => (i + 1) % messages.length);
        setCharCount(0);
      }
    }, delay);

    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [active, messages, key, msgIdx, charCount, msgLen, typeMsPerChar, holdMs]);

  return {
    text: msg.slice(0, charCount),
    messageId: msgIdx,
  };
}
