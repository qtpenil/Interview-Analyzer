"use client";

import type { ReactNode } from "react";
import { Brain } from "lucide-react";
import AuthCard from "./AuthCard";

interface AuthShellProps {
    heading: string;
    description: string;
    badge?: ReactNode;
    children: ReactNode;
}

export default function AuthShell({
    heading,
    description,
    badge,
    children,
}: AuthShellProps) {
    const year = new Date().getFullYear();

    return (
        <div className="flex min-h-screen w-full bg-background absolute inset-0 z-50">
            {/* Left Panel - Hero/Branding */}
            <div className="hidden lg:flex w-1/2 relative overflow-hidden flex-col justify-between p-12 bg-[radial-gradient(ellipse_at_top_left,_var(--gradient-start)_0%,_var(--surface)_38%,_var(--background)_75%)]">
                {/* Ambient glow orbs — signature element */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute -top-32 -left-20 w-[26rem] h-[26rem] rounded-full blur-[100px] opacity-30 animate-[pulse_7s_ease-in-out_infinite]" style={{ background: "var(--gradient-start)" }}></div>
                    <div className="absolute bottom-10 -right-24 w-[30rem] h-[30rem] rounded-full blur-[120px] opacity-20 animate-[pulse_9s_ease-in-out_infinite]" style={{ background: "var(--gradient-end)" }}></div>
                    <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,rgba(0,0,0,0.5)_100%)]"></div>
                    {/* faint animated scan lines for texture */}
                    <div
                        className="absolute inset-0 opacity-[0.06] animate-[auth-grid-pan_6s_linear_infinite]"
                        style={{
                            backgroundImage:
                                "repeating-linear-gradient(0deg, var(--gradient-end) 0px, transparent 1px, transparent 3px, var(--gradient-end) 4px)",
                        }}
                    ></div>
                    {/* floating mesh grid */}
                    <div
                        className="absolute inset-0 opacity-[0.04] animate-[auth-grid-pan_12s_linear_infinite]"
                        style={{
                            backgroundImage:
                                "linear-gradient(var(--gradient-end) 1px, transparent 1px), linear-gradient(90deg, var(--gradient-end) 1px, transparent 1px)",
                            backgroundSize: "44px 44px",
                        }}
                    ></div>
                </div>

                <div className="relative z-10 w-fit inline-flex items-center gap-3 rounded-2xl border border-accent-soft-border bg-card/40 backdrop-blur-2xl px-5 py-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-btn-primary-from to-btn-primary-to text-btn-primary-text animate-[auth-logo-glow_4s_ease-in-out_infinite]">
                        <Brain className="h-6 w-6" />
                    </div>
                    <span className="text-2xl font-extrabold text-primary tracking-tight">
                        InteReview
                    </span>
                </div>

                <div className="relative z-10 max-w-md">
                    {badge && (
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-soft border border-accent-soft-border text-secondary text-sm font-semibold mb-6">
                            {badge}
                        </div>
                    )}
                    <h1 className="text-4xl font-bold text-primary leading-tight">
                        {heading}
                    </h1>
                    <p className="mt-6 text-lg text-secondary/80 font-medium">
                        {description}
                    </p>
                </div>

                <div className="relative z-10 text-secondary/50 text-sm font-medium">
                    &copy; {year} InteReview. All rights reserved.
                </div>
            </div>

            {/* Right Panel - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center relative bg-surface p-6 sm:p-12 overflow-y-auto">

                <AuthCard>{children}</AuthCard>
            </div>
        </div>
    );
}
