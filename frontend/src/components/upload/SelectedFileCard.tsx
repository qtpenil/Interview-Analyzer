"use client";

import React from "react";
import { File, HardDrive, FileType2 } from "lucide-react";

type SelectedFileCardProps = {
  selectedFile: File;
  onClear: () => void;
  isProcessing?: boolean;
};

export default function SelectedFileCard({
  selectedFile,
  onClear,
  isProcessing = false,
}: SelectedFileCardProps) {
  const fileSizeInMB = (selectedFile.size / (1024 * 1024)).toFixed(2);
  const extension = selectedFile.name.split(".").pop()?.toUpperCase() || "FILE";

  return (
    <div className="flex h-full flex-col rounded-3xl border border-default bg-card/90 backdrop-blur-xl p-6 shadow-[var(--shadow)] transition-all duration-300 hover:shadow-[0_24px_70px_-20px_var(--shadow-glow)]">
      {/* Card label */}
      <div className="mb-5 flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted">
          Selected Interview
        </span>
        <span className="rounded-full border border-success-border bg-success-soft px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-success">
          Ready
        </span>
      </div>

      {/* File block */}
      <div className="flex items-start gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent-soft text-secondary border border-accent-soft-border shadow-[0_0_18px_-4px_var(--shadow-glow)]">
          <File className="h-6 w-6" />
        </div>

        <div className="min-w-0 flex-1">
          <h4 className="truncate text-base font-bold text-primary" title={selectedFile.name}>
            {selectedFile.name}
          </h4>
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted">
            <span className="inline-flex items-center gap-1.5">
              <HardDrive className="h-3.5 w-3.5" />
              {fileSizeInMB} MB
            </span>
            <span className="inline-flex items-center gap-1.5">
              <FileType2 className="h-3.5 w-3.5" />
              {extension}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
