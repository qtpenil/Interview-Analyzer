"use client";

import React, { useState } from "react";
import { User, Briefcase, FileText, AlertCircle } from "lucide-react";

type InterviewDetailsCardProps = {
  title: string;
  onTitleChange: (val: string) => void;
  experience: string;
  onExperienceChange: (val: string) => void;
};

export default function InterviewDetailsCard({
  title,
  onTitleChange,
  experience,
  onExperienceChange,
}: InterviewDetailsCardProps) {
  const [experienceError, setExperienceError] = useState("");

  const validateExperience = (value: string) => {
    if (!value || value.trim() === "") {
      setExperienceError("Experience years is required");
      return false;
    }
    const num = parseFloat(value);
    if (isNaN(num) || num < 0 || num > 50) {
      setExperienceError("Enter a valid number between 0 and 50");
      return false;
    }
    setExperienceError("");
    return true;
  };

  const handleExperienceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onExperienceChange(value);
    // Clear error on change if there was one
    if (experienceError) {
      validateExperience(value);
    }
  };

  const handleExperienceBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    validateExperience(e.target.value);
  };

  return (
    <div className="flex h-full flex-col rounded-3xl border border-default bg-card/90 backdrop-blur-xl p-6 shadow-[var(--shadow)] transition-all duration-300 hover:shadow-[0_24px_70px_-20px_var(--shadow-glow)]">
      {/* Card label */}
      <div className="mb-5 flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted">
          Interview Details
        </span>
      </div>

      <div className="space-y-5">
        {/* Interview Title */}
        <div>
          <label
            htmlFor="candidate-title"
            className="mb-2 flex items-center gap-1.5 text-xs font-bold text-muted uppercase tracking-wide"
          >
            <User className="h-3.5 w-3.5" />
            Interview Title
          </label>
          <input
            id="candidate-title"
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="e.g. Sandeep — Lead Backend Engineer"
            className="w-full rounded-xl border border-input-border bg-input-bg px-4 py-3 text-sm text-input-text outline-none transition-all duration-200 placeholder:text-input-placeholder hover:border-accent-soft-border focus:border-accent focus:ring-4 focus:ring-[var(--ring)]"
          />
        </div>

        {/* Claimed Experience Years */}
        <div>
          <label
            htmlFor="candidate-experience"
            className="mb-2 flex items-center gap-1.5 text-xs font-bold text-muted uppercase tracking-wide"
          >
            <Briefcase className="h-3.5 w-3.5" />
            Experience Years <span className="text-danger" aria-hidden="true">*</span>
          </label>
          <input
            id="candidate-experience"
            type="number"
            inputMode="decimal"
            min={0}
            max={50}
            step="0.5"
            value={experience}
            onChange={handleExperienceChange}
            onBlur={handleExperienceBlur}
            placeholder="e.g. 5"
            required
            aria-invalid={experienceError ? "true" : "false"}
            aria-describedby={experienceError ? "experience-error" : undefined}
            className={`w-full rounded-xl border bg-input-bg px-4 py-3 text-sm text-input-text outline-none transition-all duration-200 placeholder:text-input-placeholder hover:border-accent-soft-border focus:border-accent focus:ring-4 focus:ring-[var(--ring)] ${
              experienceError
                ? "border-danger-border focus:border-danger focus:ring-danger/20"
                : "border-input-border"
            }`}
          />
          {experienceError && (
            <p id="experience-error" className="mt-1.5 flex items-center gap-1.5 text-xs text-danger" role="alert">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {experienceError}
            </p>
          )}
          {!experienceError && (
            <p className="mt-1.5 text-xs text-muted/70">
              Required. If the AI cannot detect experience years from the interview, this value will be
              used for experience alignment scoring.
            </p>
          )}
        </div>

        <p className="flex items-center gap-1.5 pt-1 text-xs text-muted/80">
          <FileText className="h-3.5 w-3.5" />
          This title personalizes the AI analysis report. Experience years are used to score
          experience alignment.
        </p>
      </div>
    </div>
  );
}
