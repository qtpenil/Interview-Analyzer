"use client";

import React, { createContext, useContext, useState, useRef, useEffect, ReactNode } from "react";
import { uploadInterview, getInterviewStatus, cancelInterview } from "@/services/interviewApi";
import { useAuth } from "./AuthContext";

/**
 * The semantic phase of the upload → processing lifecycle. Distinguishing the
 * phase from the raw progress values lets the UI drive a single monotonic
 * progress bar without confusing upload (0-100 bytes) with processing
 * progress — previously both fed the same bar, causing the upload bar to look
 * like it reset backwards (100 → 20) when processing began.
 */
export type UploadPhase =
  | "idle"
  | "uploading"
  | "uploaded"
  | "processing"
  | "completed"
  | "failed";

interface UploadContextType {
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  title: string;
  setTitle: (title: string) => void;
  experience: string;
  setExperience: (exp: string) => void;
  isLoading: boolean;
  status: string;
  isProcessing: boolean;
  interviewId: string | null;
  isCompleted: boolean;
  error: string;
  isCancelling: boolean;
  uploadProgress: number | null;
  phase: UploadPhase;
  handleAnalyze: () => Promise<void>;
  handleCancel: () => Promise<void>;
  resetUploadState: () => void;
}

const UploadContext = createContext<UploadContextType | undefined>(undefined);

// ---------------------------------------------------------------------------
// Active-interview persistence — lets a refresh (or reopened tab) resume
// polling an in-flight interview instead of dropping the tracker.
// ---------------------------------------------------------------------------
const ACTIVE_INTERVIEW_KEY = "intereview-active-interview";
const UPLOAD_PROGRESS_KEY = "intereview-upload-progress";

function readStoredInterviewId(): string | null {
  try {
    const raw = window.localStorage.getItem(ACTIVE_INTERVIEW_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return typeof parsed?.interviewId === "string" && parsed.interviewId
      ? parsed.interviewId
      : null;
  } catch {
    return null;
  }
}

function storeActiveInterviewId(id: string | null) {
  try {
    if (id) {
      window.localStorage.setItem(
        ACTIVE_INTERVIEW_KEY,
        JSON.stringify({ interviewId: id, savedAt: Date.now() })
      );
    } else {
      window.localStorage.removeItem(ACTIVE_INTERVIEW_KEY);
    }
  } catch {
    // Storage unavailable (private mode etc.) — resume simply won't work.
  }
}

function readUploadProgress(): number | null {
  try {
    const raw = window.sessionStorage.getItem(UPLOAD_PROGRESS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return typeof parsed?.progress === "number" ? parsed.progress : null;
  } catch {
    return null;
  }
}

function storeUploadProgress(progress: number | null) {
  try {
    if (progress !== null) {
      window.sessionStorage.setItem(UPLOAD_PROGRESS_KEY, JSON.stringify({ progress }));
    } else {
      window.sessionStorage.removeItem(UPLOAD_PROGRESS_KEY);
    }
  } catch {
    // Storage unavailable — progress just won't persist across reloads.
  }
}

export function UploadProvider({ children }: { children: ReactNode }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [experience, setExperience] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState("");
  const [isCancelling, setIsCancelling] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(() => readUploadProgress());
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const resumeAttemptedRef = useRef(false);
  const { user } = useAuth();
  const prevUserEmailRef = useRef<string | null>(null);

  // Keep sessionStorage in sync with uploadProgress
  useEffect(() => {
    storeUploadProgress(uploadProgress);
  }, [uploadProgress]);

  const resetUploadState = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setSelectedFile(null);
    setTitle("");
    setExperience("");
    setIsLoading(false);
    setStatus("");
    setIsProcessing(false);
    setInterviewId(null);
    setIsCompleted(false);
    setError("");
    setIsCancelling(false);
    setUploadProgress(null);
    storeActiveInterviewId(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      return;
    }

    // Guard: don't reset progress if an upload is already in progress
    if (uploadProgress !== null) {
      return;
    }

    try {
      setIsLoading(true);
      setIsProcessing(true);
      setInterviewId(null);
      setIsCompleted(false);
      setError("");
      setStatus("Uploading interview...");
      setUploadProgress(0);

      abortControllerRef.current = new AbortController();
      const response = await uploadInterview(
        selectedFile,
        experience,
        abortControllerRef.current.signal,
        setUploadProgress
      );
      abortControllerRef.current = null;
      setUploadProgress(null);

      console.log("[handleAnalyze] upload response:", response);
      console.log("[handleAnalyze] interview_id received:", JSON.stringify(response?.interview_id));

      setInterviewId(response.interview_id);
      storeActiveInterviewId(response.interview_id);
      setStatus("File uploaded successfully.");
      
      pollInterviewStatus(response.interview_id);
    } catch (err) {
      const e = err as { code?: string; name?: string } | null;
      if (e?.code === "ERR_CANCELED" || e?.name === "CanceledError") {
        resetUploadState();
        return;
      }
      console.error(err);
      setError("Failed to upload interview.");
      setStatus("");
      setUploadProgress(null);
      setIsProcessing(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      resetUploadState();
      return;
    }

    if (!interviewId) return;

    try {
      setIsCancelling(true);
      setStatus("Cancelling interview...");

      await cancelInterview(interviewId);
      resetUploadState();
    } catch (err) {
      console.error(err);
      setError("Failed to cancel interview.");
      setIsCancelling(false);
      setStatus("");
    }
  };

  const pollInterviewStatus = (id: string) => {
    console.log("[pollInterviewStatus] polling started with id:", JSON.stringify(id));
    let consecutiveFailures = 0;
    const maxFailures = 4;

    const interval = setInterval(async () => {
      if (pollIntervalRef.current === null) {
        pollIntervalRef.current = interval;
      }
      try {
        const response = await getInterviewStatus(id);

        // Reset failure counter on success
        consecutiveFailures = 0;

        const status = response.status.toUpperCase();
        const failureMessage = response.failure_reason || response.reason || "";

        switch (status) {
          case "UPLOADED":
            setStatus("File uploaded, starting processing...");
            break;
          case "PROCESSING":
            setStatus("Processing audio...");
            break;
          case "TRANSCRIBING":
            setStatus("Transcribing interview...");
            break;
          case "ANALYZING":
            setStatus("Analyzing interview with AI...");
            break;
          case "COMPLETED":
            clearInterval(interval);
            setStatus("✅ Report ready!");
            setIsCompleted(true);
            setIsProcessing(false);
            break;
          case "CANCELLED":
            clearInterval(interval);
            setIsProcessing(false);
            setStatus("Interview cancelled.");
            break;
          case "FAILED":
            clearInterval(interval);
            setIsProcessing(false);
            setError(failureMessage || "Processing failed. Please try again.");
            setStatus("");
            break;
          default:
            // Backend may report failure with a non-standard status like
            // "not_an_interview" — treat any failure-ish status as terminal.
            if (/fail|error|invalid|not_an_/i.test(status)) {
              clearInterval(interval);
              setIsProcessing(false);
              setError(failureMessage || "Processing failed. Please try again.");
              setStatus("");
            } else {
              setStatus("Processing...");
            }
        }
      } catch (err) {
        console.error(err);
        consecutiveFailures += 1;

        // Allow a few transient failures before giving up — this prevents
        // a momentary network blip from killing the tracker when the user
        // briefly navigates away or the network hiccups.
        if (consecutiveFailures >= 4) {
          clearInterval(interval);
          setError("Lost connection while checking status. Please check your network and try again.");
          setIsProcessing(false);
        }
        // Otherwise silently retry on next interval
      }
    }, 4000);
  };

  // Reset when the signed-in user changes. Skipped on first mount so an
  // in-flight interview (restored below) isn't wiped on a normal refresh.
  useEffect(() => {
    const currentUserEmail = user?.email ?? null;

    if (prevUserEmailRef.current !== null && prevUserEmailRef.current !== currentUserEmail) {
      resetUploadState();
    }
    prevUserEmailRef.current = currentUserEmail;
  }, [user?.email]);

  // Resume tracking an in-flight interview after a page refresh. Runs once,
  // once the user is authenticated.
  useEffect(() => {
    if (!user || resumeAttemptedRef.current) return;
    resumeAttemptedRef.current = true;

    const storedId = readStoredInterviewId();
    if (!storedId) return;

    let cancelled = false;

    (async () => {
      try {
        const response = await getInterviewStatus(storedId);
        if (cancelled) return;

        const resumedStatus = response.status.toUpperCase();
        const failureMessage = response.failure_reason || response.reason || "";

        setInterviewId(storedId);

        switch (resumedStatus) {
          case "COMPLETED":
            setStatus("✅ Report ready!");
            setIsCompleted(true);
            setIsProcessing(false);
            break;
          case "CANCELLED":
            setIsProcessing(false);
            setStatus("Interview cancelled.");
            break;
          case "FAILED":
            setIsProcessing(false);
            setError(failureMessage || "Processing failed. Please try again.");
            setStatus("");
            break;
          default:
            if (/fail|error|invalid|not_an_/i.test(resumedStatus)) {
              setIsProcessing(false);
              setError(failureMessage || "Processing failed. Please try again.");
              setStatus("");
            } else {
              // Still in flight — resume polling until terminal status.
              setIsProcessing(true);
              setIsCompleted(false);
              setStatus("Resuming processing...");
              pollInterviewStatus(storedId);
            }
        }
      } catch {
        if (!cancelled) {
          // Interview unreachable (deleted / bad id) — drop stale entry.
          storeActiveInterviewId(null);
          setInterviewId(null);
          setIsProcessing(false);
          setStatus("");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [user]);

  // Derive the lifecycle phase from the authoritative state atoms. Derived
  // (rather than a second parallel setState) so it can never drift from the
  // source-of-truth values and no new reset path is introduced.
  const phase: UploadPhase = isCompleted
    ? "completed"
    : error && !isProcessing
    ? "failed"
    : uploadProgress !== null
    ? "uploading"
    : isProcessing
    ? "processing"
    : "idle";

  return (
    <UploadContext.Provider
      value={{
        selectedFile,
        setSelectedFile,
        title,
        setTitle,
        experience,
        setExperience,
        isLoading,
        status,
        isProcessing,
        interviewId,
        isCompleted,
        error,
        isCancelling,
        uploadProgress,
        phase,
        handleAnalyze,
        handleCancel,
        resetUploadState,
      }}
    >
      {children}
    </UploadContext.Provider>
  );
}

export function useUpload() {
  const context = useContext(UploadContext);
  if (context === undefined) {
    throw new Error("useUpload must be used within an UploadProvider");
  }
  return context;
}
