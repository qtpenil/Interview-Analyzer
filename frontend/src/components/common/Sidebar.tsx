"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Brain,
  UploadCloud,
  FolderClosed,
  BarChart3,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";

type SidebarContentProps = {
  onClose?: () => void;
  onLogout: () => void;
  pathname: string;
  userName?: string;
  userEmail?: string;
};

function AccountMenu({
  onLogout,
  userName,
  userEmail,
}: {
  onLogout: () => void;
  userName?: string;
  userEmail?: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  // Close on Escape, return focus to trigger
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <div ref={containerRef}>
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
        className={`flex w-full items-center gap-3 border border-default bg-surface/50 px-3 py-2.5 text-left transition-all duration-200 hover:border-accent-soft-border hover:bg-accent-soft focus:outline-none focus-visible:ring-4 ${
          open ? "rounded-t-xl border-b-0" : "rounded-xl"
        }`}
        style={{ ["--tw-ring-color" as string]: "var(--ring)" }}
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-btn-primary-from to-btn-primary-to text-btn-primary-text text-sm font-bold shadow-[0_0_14px_-2px_var(--shadow-glow)]">
          {(userName || userEmail || "U").charAt(0).toUpperCase()}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-primary">
            {userName || "User"}
          </span>
          <span className="block truncate text-xs text-muted">
            {userEmail}
          </span>
        </span>
      </button>

      {/* Dropdown — in-flow (not overlaid), animates height so it pushes
          the account card and theme toggle upward as it opens/closes.
          The inner panel starts translated fully behind the account card
          (translate-y -100%) and slides straight down into place, so it
          reads as emerging from underneath the card rather than fading in. */}
      <div
        className="grid transition-[grid-template-rows] duration-250 ease-out"
        style={{ gridTemplateRows: open ? "1fr" : "0fr" }}
      >
        <div className="overflow-hidden">
          <div
            role="menu"
            aria-hidden={!open}
            className={`rounded-b-xl border border-t-0 border-default bg-surface shadow-[var(--shadow)] transition-[transform,opacity] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              open
                ? "translate-y-0 opacity-100"
                : "-translate-y-full opacity-0"
            }`}
          >
            <button
              type="button"
              role="menuitem"
              tabIndex={open ? 0 : -1}
              onClick={() => {
                setOpen(false);
                try {
                  onLogout();
                } catch (err) {
                  console.error("Logout failed:", err);
                }
              }}
              className="flex w-full items-center justify-center gap-1.5 py-1.5 text-xs text-danger transition-colors duration-150 hover:bg-danger-soft focus:outline-none focus-visible:bg-danger-soft"
            >
              <LogOut className="h-3.5 w-3.5 shrink-0" strokeWidth={2.2} />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SidebarContent({
  onClose,
  onLogout,
  pathname,
  userName,
  userEmail,
}: SidebarContentProps) {
  const menuItems = [
    {
      name: "Upload Analyzer",
      href: "/dashboard",
      icon: UploadCloud,
    },
    {
      name: "Analytics",
      href: "/analytics",
      icon: BarChart3,
    },
    {
      name: "Interviews Repository",
      href: "/interviews",
      icon: FolderClosed,
    },
  ];

  const isActive = (href: string) => {
    return pathname.startsWith(href);
  };

  return (
    <div className="flex flex-col h-full bg-surface border-r border-default">
      {/* Branding Logo Header */}
      <div className="p-6 border-b border-default flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_20px_-3px_var(--shadow-glow)] group-hover:scale-105 transition-transform duration-200">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-extrabold text-primary tracking-tight text-md">
              InteReview
            </h2>
          </div>
        </Link>
        <button
          type="button"
          onClick={onClose}
          className="md:hidden p-1.5 rounded-lg text-muted hover:bg-surface-hover/50 hover:text-primary"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-4 py-6 space-y-7 overflow-y-auto">
        <nav className="space-y-1.5">
          {menuItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-xl text-sm font-semibold transition-all duration-200 group ${active
                    ? "bg-accent-soft text-secondary border border-accent px-3 py-3"
                    : "text-secondary/50 hover:bg-surface-hover/50 hover:text-primary border border-transparent px-3 py-2.5"
                  }`}
              >
                <item.icon
                  className={`h-5 w-5 shrink-0 ${active
                      ? "text-secondary"
                      : "text-muted group-hover:text-secondary"
                    }`}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User Session Info Card footer */}
      <div className="px-4 pt-4 pb-4 border-t border-default bg-surface/60 space-y-3">
        <div title="Toggle light / dark theme" className="flex justify-center">
          <ThemeToggle className="transition-transform duration-200 ease-out hover:scale-[1.03] active:scale-95" />
        </div>

        <AccountMenu
          onLogout={onLogout}
          userName={userName}
          userEmail={userEmail}
        />
      </div>
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, isLoggedIn, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (
    pathname === "/" ||
    pathname === "/login" ||
    pathname === "/register" ||
    pathname.startsWith("/forgot-password")
  ) {
    return null;
  }

  if (!isLoggedIn) {
    return null;
  }

  const userProps = {
    userName: user?.name,
    userEmail: user?.email,
  };

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:block w-64 h-screen sticky top-0 shrink-0 z-20">
        <SidebarContent onLogout={logout} pathname={pathname} {...userProps} />
      </aside>

      {/* Mobile Header Bar */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-surface border-b border-default w-full z-20">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_15px_-3px_var(--shadow-glow)]">
            <Brain className="h-4.5 w-4.5" />
          </div>
          <span className="font-extrabold text-primary tracking-tight text-sm">
            InteReview
          </span>
        </Link>
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="p-1.5 rounded-lg border border-default text-secondary/50 hover:bg-surface-hover/50 hover:text-primary"
        >
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {/* Mobile Drawer Slide-out Sidebar Overlay */}
      {isOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Overlay backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer panel */}
          <div className="relative w-72 max-w-[80%] h-full animate-[slideInLeft_0.3s_ease]">
            <SidebarContent
              onClose={() => setIsOpen(false)}
              onLogout={logout}
              pathname={pathname}
              {...userProps}
            />
          </div>
        </div>
      )}
    </>
  );
}