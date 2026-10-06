"use client";

import Link from "next/link";
import FileUpload from "@/components/upload/FileUpload";
import SelectedFileCard from "@/components/upload/SelectedFileCard";
import InterviewDetailsCard from "@/components/upload/InterviewDetailsCard";
import AnalyzeInterviewButton from "@/components/upload/AnalyzeInterviewButton";
import ProcessingTracker from "@/components/upload/ProcessingTracker";
import CompletionBanner from "@/components/upload/CompletionBanner";
import UploadRecentSidebar from "@/components/upload/UploadRecentSidebar";
import { downloadReport } from "@/services/interviewApi";
import { useUpload } from "@/context/UploadContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function DashboardPage() {
  const authStatus = useRequireAuth();

  const {
    selectedFile,
    setSelectedFile,
    title,
    setTitle,
    experience,
    setExperience,
    isLoading,
    isProcessing,
    isCompleted,
    error,
    interviewId,
    uploadProgress,
    handleAnalyze,
    resetUploadState,
  } = useUpload();

  if (authStatus === "checking") {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-secondary/50">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-soft-border border-t-secondary" />
          <span className="text-sm">Verifying your session…</span>
        </div>
      </main>
    );
  }

  if (authStatus === "unauthed") {
    // AuthContext will redirect to /login; render nothing to avoid flash
    return null;
  }

  const handleDownload = () => {
    if (interviewId) downloadReport(interviewId);
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setTitle(file.name.replace(/\.[^/.]+$/, ""));
  };

  const showError = Boolean(error) && !isProcessing && !isCompleted;

  return (
    <main className="relative px-4 py-6 pb-24 sm:px-6 lg:py-8 lg:pb-16">
      <div className="mx-auto max-w-8xl">
        {/* Header */}
        <header className="mb-8 animate-[fade-up_0.6s_ease-out]">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-primary">
            AI Interview Analyzer
          </h1>
          <p className="mt-2 max-w-2xl text-sm sm:text-base leading-relaxed text-secondary/60">
            Upload your candidate recording and receive automated AI feedback,
            scoring, and a downloadable report.
          </p>
          <div className="mt-6 border-b border-default" />
        </header>

        {/* Responsive Grid: Upload Section + Recent & Stats Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Main Upload Column (8 cols on desktop) */}
          <div className="lg:col-span-8 space-y-8">
            {/* Upload card (only before a file is selected) */}
            {!selectedFile && (
              <div className="animate-[fade-up_0.6s_ease-out_0.05s]">
                <FileUpload
                  selectedFile={selectedFile}
                  onFileSelect={handleFileSelect}
                />
              </div>
            )}

            {/* Two balanced info cards */}
            {selectedFile && (
              <div className="grid animate-[fade-up_0.6s_ease-out] gap-6 md:grid-cols-2">
                <SelectedFileCard
                  selectedFile={selectedFile}
                  onClear={() => {
                    setSelectedFile(null);
                    setTitle("");
                  }}
                  isProcessing={isProcessing || isLoading}
                />
                <InterviewDetailsCard
                  title={title}
                  onTitleChange={setTitle}
                  experience={experience}
                  onExperienceChange={setExperience}
                />
              </div>
            )}

            {/* Prominent analyze / reset action */}
            {selectedFile && !isProcessing && !isLoading && !isCompleted && (
              <div className="animate-[fade-up_0.6s_ease-out_0.1s]">
                <AnalyzeInterviewButton
                  hasFile={Boolean(selectedFile)}
                  hasExperience={Boolean(experience && experience.trim() !== "")}
                  isProcessing={isProcessing || isLoading}
                  isUploading={uploadProgress !== null}
                  isCompleted={isCompleted}
                  onAnalyze={handleAnalyze}
                  onReset={resetUploadState}
                />
              </div>
            )}

            {/* Processing progress tracker */}
            {(isProcessing || isLoading) && (
              <div className="animate-[fade-up_0.6s_ease-out]">
                <ProcessingTracker />
              </div>
            )}

            {/* Error (non-processing) */}
            {showError && (
              <div
                role="alert"
                className="flex animate-[fade-up_0.6s_ease-out] items-center gap-2 rounded-2xl border border-danger-border bg-danger-soft px-4 py-3 text-sm text-danger"
              >
                <span className="font-semibold">Something went wrong:</span>
                {error}
              </div>
            )}

            {/* Completion */}
            {isCompleted && interviewId && (
              <div className="animate-[fade-up_0.6s_ease-out]">
                <CompletionBanner
                  interviewId={interviewId}
                  onDownload={handleDownload}
                  onReset={resetUploadState}
                />
              </div>
            )}

            {/* Browse existing interviews shortcut */}
            {!selectedFile && (
              <Link
                href="/interviews"
                className="group inline-flex animate-[fade-up_0.6s_ease-out_0.15s] items-center gap-2 text-sm font-semibold text-secondary transition-colors hover:text-primary"
              >
                Or browse your existing interviews
                <span className="transition-transform duration-200 group-hover:translate-x-1">
                  →
                </span>
              </Link>
            )}
          </div>

          {/* Right Sidebar: Quick Stats & Recent Uploads (4 cols on desktop) */}
          <div className="lg:col-span-4 lg:sticky lg:top-6 animate-[fade-up_0.6s_ease-out_0.1s]">
            <UploadRecentSidebar />
          </div>
        </div>
      </div>
    </main>
  );
}
