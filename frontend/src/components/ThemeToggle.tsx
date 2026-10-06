"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export default function ThemeToggle({
  className = "",
}: {
  className?: string;
}) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      onClick={toggleTheme}
      className={`group relative inline-flex h-8 w-[5.5rem] shrink-0 items-center rounded-full border border-default bg-surface/70 px-1 transition-colors duration-300 ease-out hover:border-accent-soft-border hover:bg-surface-hover focus:outline-none focus-visible:ring-4 focus-visible:ring-offset-2 focus-visible:ring-offset-surface ${
        isDark ? "bg-surface-hover" : ""
      } ${className}`}
      style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
    >
      {/* Fixed end icons */}
      <Sun
        className={`pointer-events-none absolute left-[0.45rem] h-3.5 w-3.5 transition-all duration-300 ease-out ${
          isDark
            ? "scale-90 text-white opacity-70"
            : "scale-110 text-warning opacity-100 drop-shadow-[0_0_6px_var(--shadow-glow)]"
        }`}
        strokeWidth={2.4}
        aria-hidden="true"
      />
      <Moon
        className={`pointer-events-none absolute right-[0.45rem] h-3.5 w-3.5 transition-all duration-300 ease-out ${
          isDark
            ? "scale-110 text-secondary opacity-100 drop-shadow-[0_0_6px_var(--shadow-glow)]"
            : "scale-90 text-black opacity-70"
        }`}
        strokeWidth={2.4}
        aria-hidden="true"
      />

      {/* Sliding thumb */}
      <span
        aria-hidden="true"
        className="pointer-events-none relative z-10 flex h-6 w-6 items-center justify-center rounded-full shadow-[0_0_14px_-2px_var(--shadow-glow)] transition-transform duration-[280ms] ease-[cubic-bezier(0.65,0,0.35,1)] group-active:scale-90"
        style={{
          transform: isDark ? "translateX(3.5rem)" : "translateX(0)",
          background:
            "linear-gradient(to right, var(--gradient-start), var(--gradient-end))",
        }}
      >
        <Moon
          className={`absolute h-3.5 w-3.5 text-btn-primary-text transition-[opacity,transform] duration-[280ms] ease-[cubic-bezier(0.65,0,0.35,1)] ${
            isDark ? "scale-100 opacity-100" : "scale-0 opacity-0"
          }`}
          strokeWidth={2.4}
        />
        <Sun
          className={`absolute h-3.5 w-3.5 text-btn-primary-text transition-[opacity,transform] duration-[280ms] ease-[cubic-bezier(0.65,0,0.35,1)] ${
            isDark ? "scale-0 opacity-0" : "scale-100 opacity-100"
          }`}
          strokeWidth={2.4}
        />
      </span>
    </button>
  );
}