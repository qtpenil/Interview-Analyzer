"use client";

import { useEffect, useState } from "react";
import { ChevronUp } from "lucide-react";

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 300);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <button
      type="button"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      aria-label="Scroll to top"
      className={`fixed bottom-6 right-6 z-50 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] active:translate-y-0 ${
        visible
          ? "scale-100 opacity-100 pointer-events-auto"
          : "scale-75 opacity-0 pointer-events-none"
      }`}
    >
      <ChevronUp className="h-5 w-5" />
    </button>
  );
}
