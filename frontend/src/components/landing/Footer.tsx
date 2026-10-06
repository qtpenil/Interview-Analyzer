"use client";

import Link from "next/link";
import { Brain, Code2, Mail } from "lucide-react";
import ScrollLink from "./ScrollLink";
import { useAuth } from "@/context/AuthContext";

const footerNav = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Workflow", href: "#workflow" },
      { label: "Reports", href: "#reports" },
      { label: "FAQ", href: "#faq" },
    ],
  },
  {
    title: "Account",
    links: [
      { label: "Sign Up", href: "/register" },
      { label: "Login", href: "/login" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
      { label: "Contact", href: "#" },
    ],
  },
];

export default function Footer() {
  const { isLoggedIn } = useAuth();

  const accountLinks = isLoggedIn
    ? [{ label: "Dashboard", href: "/dashboard" }]
    : [
        { label: "Sign Up", href: "/register" },
        { label: "Login", href: "/login" },
      ];

  const visibleNav = footerNav.map((group) =>
    group.title === "Account" ? { ...group, links: accountLinks } : group
  );

  return (
    <footer className="border-t border-default bg-surface/40">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)]">
                <Brain className="h-5 w-5" />
              </div>
              <span className="font-extrabold text-primary tracking-tight text-base">
                InteReview
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-6 text-secondary/70">
              Turn every interview into actionable, evidence-based insights with AI.
            </p>
            <div className="mt-5 flex items-center gap-3">
              <a
                href="#"
                aria-label="GitHub"
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-default text-secondary/60 transition-colors hover:bg-surface-hover/50 hover:text-primary"
              >
                <Code2 className="h-4 w-4" />
              </a>
              <a
                href="#"
                aria-label="Contact"
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-default text-secondary/60 transition-colors hover:bg-surface-hover/50 hover:text-primary"
              >
                <Mail className="h-4 w-4" />
              </a>
            </div>
          </div>

          {visibleNav.map((group) => (
            <div key={group.title}>
              <h3 className="text-xs font-bold uppercase tracking-widest text-secondary">
                {group.title}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {group.links.map((link) => (
                  <li key={link.label}>
                    <ScrollLink
                      href={link.href}
                      className="text-sm text-secondary/70 transition-colors hover:text-primary"
                    >
                      {link.label}
                    </ScrollLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-default pt-6 sm:flex-row">
          <p className="text-xs text-muted">
            &copy; {new Date().getFullYear()} InteReview. All rights reserved.
          </p>
          <p className="text-xs text-muted">
            Built for fair, fast, and insightful hiring.
          </p>
        </div>
      </div>
    </footer>
  );
}
