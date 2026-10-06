"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Brain, Menu, X, LayoutDashboard } from "lucide-react";
import Button from "./Button";
import ScrollLink from "./ScrollLink";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/context/AuthContext";

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Workflow", href: "#workflow" },
  { label: "Reports", href: "#reports" },
  { label: "FAQ", href: "#faq" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { isLoggedIn } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "border-b border-default bg-background/70 backdrop-blur-xl shadow-[var(--shadow)]"
          : "border-b border-transparent bg-transparent"
      }`}
    >
      <nav
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8"
        aria-label="Primary"
      >
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)] group-hover:scale-105 transition-transform duration-200">
            <Brain className="h-5 w-5" />
          </div>
          <span className="font-extrabold text-primary tracking-tight text-base">
            InteReview
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <ScrollLink
              key={link.href}
              href={link.href}
              className="rounded-lg px-3.5 py-2 text-sm font-semibold text-secondary/70 hover:text-primary hover:bg-surface-hover/50 transition-colors"
            >
              {link.label}
            </ScrollLink>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-2.5">
          <ThemeToggle />
          {isLoggedIn ? (
            <Button href="/dashboard" variant="primary" size="sm">
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Button>
          ) : (
            <>
              <Button href="/login" variant="ghost" size="sm">
                Login
              </Button>
              <Button href="/register" variant="primary" size="sm">
                Sign Up Free
              </Button>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="md:hidden p-2 rounded-lg border border-default text-secondary/70 hover:bg-surface-hover/50 hover:text-primary"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {open && (
        <div className="md:hidden border-t border-default bg-background/95 backdrop-blur-xl px-5 py-4 space-y-1">
          {navLinks.map((link) => (
            <ScrollLink
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-secondary/70 hover:text-primary hover:bg-surface-hover/50 transition-colors"
            >
              {link.label}
            </ScrollLink>
          ))}
          <div className="flex flex-col gap-2 pt-3">
            {isLoggedIn ? (
              <Button href="/dashboard" variant="primary" size="sm" className="w-full">
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </Button>
            ) : (
              <>
                <Button href="/login" variant="secondary" size="sm" className="w-full">
                  Login
                </Button>
                <Button href="/register" variant="primary" size="sm" className="w-full">
                  Sign Up Free
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
