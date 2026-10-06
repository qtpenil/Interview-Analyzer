"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  className?: string;
  /** Stagger delay in milliseconds */
  delay?: number;
  /** Distance to slide up from, in pixels */
  y?: number;
  as?: "div" | "section" | "li" | "span";
};

/**
 * Lightweight scroll-reveal wrapper. Uses IntersectionObserver + CSS
 * transitions to deliver fade-up / stagger / slide-up effects without an
 * animation dependency.
 *
 * Starts hidden on both server and client (identical initial render) and
 * reveals once scrolled into view, avoiding hydration mismatches.
 */
export default function Reveal({
  children,
  className = "",
  delay = 0,
  y = 24,
  as = "div",
}: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const Tag = as as "div";

  return (
    <Tag
      ref={ref as React.Ref<HTMLDivElement>}
      className={`transition-all duration-700 ease-out will-change-transform ${
        visible ? "opacity-100" : "opacity-0 pointer-events-none"
      } ${className}`}
      style={{
        transitionDelay: `${delay}ms`,
        transform: visible ? "translateY(0)" : `translateY(${y}px)`,
      }}
    >
      {children}
    </Tag>
  );
}
