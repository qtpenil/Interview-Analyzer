"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useSmoothScroll } from "@/hooks/useSmoothScroll";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg";

type ButtonProps = {
  children: ReactNode;
  href?: string;
  onClick?: (e?: React.MouseEvent<HTMLAnchorElement | HTMLButtonElement>) => void;
  className?: string;
  variant?: Variant;
  size?: Size;
  type?: "button" | "submit";
  "aria-label"?: string;
  external?: boolean;
};

const base =
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]";

const variants: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:-translate-y-0.5 active:translate-y-0",
  secondary:
    "border border-btn-secondary-border bg-btn-secondary-bg text-btn-secondary-text hover:bg-surface-hover hover:-translate-y-0.5 active:translate-y-0",
  ghost:
    "text-secondary hover:text-primary hover:bg-surface-hover/50",
};

const sizes: Record<Size, string> = {
  sm: "px-4 py-2 text-xs",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3.5 text-base",
};

export default function Button({
  children,
  href,
  onClick,
  className = "",
  variant = "primary",
  size = "md",
  type = "button",
  "aria-label": ariaLabel,
  external = false,
}: ButtonProps) {
  const classes = `${base} ${variants[variant]} ${sizes[size]} ${className}`;
  const smoothScroll = useSmoothScroll();

  if (href) {
    if (external) {
      return (
        <a
          href={href}
          onClick={onClick}
          className={classes}
          aria-label={ariaLabel}
          target="_blank"
          rel="noreferrer"
        >
          {children}
        </a>
      );
    }
    if (href.startsWith("#")) {
      const handleHashClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
        onClick?.(e);
        smoothScroll(e, href);
      };
      return (
        <a
          href={href}
          onClick={handleHashClick}
          className={classes}
          aria-label={ariaLabel}
        >
          {children}
        </a>
      );
    }
    return (
      <Link href={href} onClick={onClick} className={classes} aria-label={ariaLabel}>
        {children}
      </Link>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      className={classes}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}
