"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileVideo, FileAudio } from "lucide-react";

type FileUploadProps = {
  selectedFile: File | null;
  onFileSelect: (file: File) => void;
};

const ACCEPTED_EXTENSIONS = ["mp4", "mov", "webm", "mp3", "wav"];
const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024;

function validateFile(file: File): { ok: boolean; message?: string } {
  const extension = file.name.split(".").pop()?.toLowerCase() || "";
  const hasValidExtension = ACCEPTED_EXTENSIONS.includes(extension);
  const hasValidMime = file.type.startsWith("video/") || file.type.startsWith("audio/");

  if (!hasValidExtension && !hasValidMime) {
    return {
      ok: false,
      message: "Unsupported file type. Please upload MP4, MOV, WEBM, MP3 or WAV.",
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { ok: false, message: "File is too large. Maximum size is 2 GB." };
  }

  return { ok: true };
}

export default function FileUpload({
  selectedFile,
  onFileSelect,
}: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const selectFile = (file: File | undefined) => {
    setError("");
    if (!file) return;

    const result = validateFile(file);
    if (!result.ok) {
      setError(result.message || "Invalid file.");
      return;
    }

    onFileSelect(file);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    selectFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    selectFile(event.dataTransfer.files?.[0]);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
  };

  const openPicker = () => inputRef.current?.click();

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`
        group relative flex flex-col items-center justify-center overflow-hidden rounded-3xl border-2 border-dashed p-10 text-center backdrop-blur-xl transition-all duration-300 bg-card/60 shadow-[var(--shadow)]
        ${
          isDragActive
            ? "border-accent bg-accent-soft ring-4 ring-[var(--ring)] scale-[1.01]"
            : "border-default hover:border-accent hover:bg-accent-soft"
        }
      `}
    >
      {/* Soft inner glow */}
      <div
        className="pointer-events-none absolute inset-0 opacity-60"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, var(--accent-soft) 0%, transparent 70%)",
        }}
      />

      <div className="relative flex flex-col items-center justify-center">
        {/* Animated Icon Container */}
        <div
          className={`
            flex h-20 w-20 items-center justify-center rounded-2xl mb-5 transition-all duration-300
            ${
              isDragActive
                ? "scale-110 shadow-[0_0_30px_-3px_var(--shadow-glow)] text-btn-primary-text"
                : "bg-accent-soft text-secondary border border-accent-soft-border"
            }
          `}
          style={
            isDragActive
              ? {
                  background:
                    "linear-gradient(to right, var(--gradient-start), var(--gradient-end))",
                }
              : undefined
          }
        >
          {isDragActive ? (
            <UploadCloud className="h-9 w-9 animate-bounce" />
          ) : selectedFile ? (
            selectedFile.type.includes("audio") ? (
              <FileAudio className="h-9 w-9" />
            ) : (
              <FileVideo className="h-9 w-9" />
            )
          ) : (
            <UploadCloud className="h-9 w-9 transition-transform duration-300 group-hover:-translate-y-1" />
          )}
        </div>

        <h3 className="text-2xl font-bold text-primary tracking-tight">
          {selectedFile
            ? "Interview recording selected"
            : "Upload your interview file"}
        </h3>

        <p className="mt-2.5 text-sm text-secondary/60 max-w-md mx-auto leading-relaxed">
          {selectedFile
            ? `You selected "${selectedFile.name}". Add candidate details on the right, then start the analysis below.`
            : "Drag & drop your interview recording here, or browse your device. We'll transcribe and analyze it with AI."}
        </p>

        {!selectedFile && (
          <div className="mt-7 flex flex-col items-center">
            <button
              type="button"
              onClick={openPicker}
              className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-7 py-3.5 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] transition-all duration-200 hover:from-btn-primary-to hover:to-btn-primary-from hover:-translate-y-0.5 hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] active:translate-y-0 active:scale-[0.98] focus:outline-none focus-visible:ring-4"
              style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
            >
              <UploadCloud className="h-5 w-5" />
              Choose File
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".mp4,.mov,.webm,.mp3,.wav"
              className="hidden"
              onChange={handleFileChange}
            />
            <span className="mt-4 text-xs text-muted font-semibold tracking-wide uppercase">
              Supported: Video (MP4, MOV, WEBM) · Audio (MP3, WAV)
            </span>
            {error && (
              <span role="alert" className="mt-3 text-sm font-semibold text-danger">
                {error}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
