"use client";

import type { ReactNode } from "react";
import { Brain } from "lucide-react";

interface AuthCardProps {
    children: ReactNode;
    className?: string;
}

export default function AuthCard({
    children,
    className = "",
}: AuthCardProps) {
    return (
        <div className={`relative w-full max-w-md my-auto ${className}`}>
            <div className="relative rounded-[2rem] border border-accent-soft-border bg-card p-8 sm:p-10 shadow-[var(--shadow)] transition-all duration-300 hover:shadow-[var(--shadow),0_0_70px_-8px_var(--shadow-glow)] animate-[auth-fade-up_0.7s_cubic-bezier(0.22,1,0.36,1)]">
                <div className="lg:hidden flex justify-center mb-6">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-btn-primary-from to-btn-primary-to text-btn-primary-text shadow-[0_0_25px_var(--shadow-glow)]">
                        <Brain className="h-7 w-7" />
                    </div>
                </div>
                {children}
            </div>
        </div>
    );
}
