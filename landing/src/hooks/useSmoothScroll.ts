"use client";

import { useCallback } from "react";

// Smoothly scrolls to an in-page anchor (#id) with a small delay and a brief
// highlight pulse on the target. Returns true when it handled the click.
export function useSmoothScroll(offset = 96, delay = 180) {
  return useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
      if (!href.startsWith("#")) return false;
      const id = href.slice(1);
      if (!id) return false;

      const el = document.getElementById(id);
      if (!el) return false;

      e.preventDefault();

      window.setTimeout(() => {
        const top =
          el.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: "smooth" });

        el.classList.remove("scroll-highlight");
        // force reflow so the animation can restart on repeat clicks
        void el.offsetWidth;
        el.classList.add("scroll-highlight");
        window.setTimeout(
          () => el.classList.remove("scroll-highlight"),
          1400
        );
      }, delay);

      return true;
    },
    [offset, delay]
  );
}
