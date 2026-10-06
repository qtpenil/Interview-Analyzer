"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  AlertCircle,
} from "lucide-react";

type DemoVideoProps = {
  videoSrc?: string;
  posterSrc?: string;
  className?: string;
};

const formatTime = (seconds: number) => {
  if (!Number.isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
};

export default function DemoVideo({
  videoSrc = "/videos/demo.mp4",
  posterSrc,
  className = "",
}: DemoVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [hasStarted, setHasStarted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(false);

  const showControls = useCallback(() => {
    setControlsVisible(true);
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    hideTimerRef.current = setTimeout(() => {
      const video = videoRef.current;
      if (video && !video.paused) {
        setControlsVisible(false);
      }
    }, 2500);
  }, []);

  useEffect(() => {
    return () => {
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, []);

  useEffect(() => {
    const onFullscreenChange = () =>
      setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      void video.play().catch(() => setError(true));
    } else {
      video.pause();
    }
  }, []);

  const seek = (clientX: number) => {
    const bar = progressRef.current;
    const video = videoRef.current;
    if (!bar || !video || !video.duration) return;
    const rect = bar.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    video.currentTime = ratio * video.duration;
    setCurrentTime(video.currentTime);
  };

  const handleProgressPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    progressRef.current?.setPointerCapture(e.pointerId);
    seek(e.clientX);
  };

  const handleProgressPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.buttons !== 1) return;
    seek(e.clientX);
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
    setIsMuted(video.muted);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      void containerRef.current?.requestFullscreen?.();
    } else {
      void document.exitFullscreen?.();
    }
  };

  const progressPct = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      onMouseMove={showControls}
      className={`group relative w-full overflow-hidden rounded-2xl border border-default bg-black ${
        isFullscreen ? "rounded-none border-0" : "shadow-[var(--shadow)]"
      } ${className}`}
    >
      <video
        ref={videoRef}
        playsInline
        preload="metadata"
        poster={posterSrc}
        onClick={togglePlay}
        onPlay={() => {
          setIsPlaying(true);
          setHasStarted(true);
        }}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
        onTimeUpdate={() =>
          setCurrentTime(videoRef.current?.currentTime ?? 0)
        }
        onLoadedMetadata={() => setDuration(videoRef.current?.duration ?? 0)}
        onVolumeChange={() => setIsMuted(videoRef.current?.muted ?? false)}
        onError={() => setError(true)}
        className="aspect-video w-full cursor-pointer"
      >
        <source src={videoSrc} type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {!hasStarted && !error && (
        <button
          type="button"
          onClick={togglePlay}
          aria-label="Play demo video"
          className="absolute inset-0 z-10 flex items-center justify-center bg-gradient-to-b from-black/30 via-black/40 to-black/60 transition-opacity duration-200 hover:opacity-90 focus:outline-none focus-visible:ring-4"
          style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_30px_-4px_var(--shadow-glow)] transition-transform duration-200 hover:scale-110 sm:h-20 sm:w-20">
            <Play className="h-7 w-7 translate-x-0.5 fill-current sm:h-9 sm:w-9" />
          </span>
        </button>
      )}

      {error && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-black/70 px-6 text-center">
          <AlertCircle className="h-8 w-8 text-warning" />
          <p className="text-sm font-medium text-white/85">
            Couldn&apos;t load the demo video. Please check the file format in
            public/videos/demo.mp4.
          </p>
        </div>
      )}

      <div
        onClick={(e) => e.stopPropagation()}
        className={`absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-3 pb-2 pt-8 transition-opacity duration-300 ${
          controlsVisible
            ? "opacity-100"
            : "pointer-events-none opacity-0"
        }`}
      >
        <div
          ref={progressRef}
          onPointerDown={handleProgressPointerDown}
          onPointerMove={handleProgressPointerMove}
          className="mb-2 flex h-4 cursor-pointer items-center"
        >
          <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-white/15">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-btn-primary-from to-btn-primary-to"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
        <div className="flex items-center gap-3 text-white">
          <button
            type="button"
            onClick={togglePlay}
            aria-label={isPlaying ? "Pause demo video" : "Play demo video"}
            className="rounded-lg p-1 text-white/90 transition-colors hover:text-white focus:outline-none focus-visible:ring-4"
            style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
          >
            {isPlaying ? (
              <Pause className="h-5 w-5 fill-current" />
            ) : (
              <Play className="h-5 w-5 fill-current" />
            )}
          </button>
          <span className="text-xs font-medium tabular-nums text-white/80">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
          <div className="flex-1" />
          <button
            type="button"
            onClick={toggleMute}
            aria-label={isMuted ? "Unmute" : "Mute"}
            className="rounded-lg p-1 text-white/90 transition-colors hover:text-white focus:outline-none focus-visible:ring-4"
            style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
          >
            {isMuted ? (
              <VolumeX className="h-5 w-5" />
            ) : (
              <Volume2 className="h-5 w-5" />
            )}
          </button>
          <button
            type="button"
            onClick={toggleFullscreen}
            aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            className="rounded-lg p-1 text-white/90 transition-colors hover:text-white focus:outline-none focus-visible:ring-4"
            style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
          >
            {isFullscreen ? (
              <Minimize className="h-5 w-5" />
            ) : (
              <Maximize className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
