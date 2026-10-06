"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Mail, Lock, Eye, EyeOff } from "lucide-react";
import AuthShell from "@/components/auth/AuthShell";
import { validateEmail } from "@/lib/validators";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [emailError, setEmailError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { login, isLoggedIn, isLoading } = useAuth();

    useEffect(() => {
        if (!isLoading && isLoggedIn) {
            router.push("/dashboard");
        }
    }, [isLoggedIn, isLoading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setEmailError("");

        const emailErrorMsg = validateEmail(email);
        if (emailErrorMsg) {
            setEmailError(emailErrorMsg);
            return;
        }

        setIsSubmitting(true);

        try {
            await login({ email: email.trim(), password: password.trim() });
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to login. Please check your credentials.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthShell
            heading="Streamline your hiring process with AI insights."
            description="Upload interview recordings and let our advanced AI extract deep insights, evaluate skills, and provide comprehensive hiring recommendations in minutes."
        >
            <div>
                <h2 className="text-center text-3xl font-extrabold tracking-tight text-primary">
                    Welcome back
                </h2>
                <p className="mt-2 text-center text-sm text-secondary/50">
                    Don't have an account?{" "}
                    <Link href="/register" className="font-bold text-secondary hover:text-primary transition-colors">
                        Sign up for free
                    </Link>
                </p>
            </div>

            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                <div className="space-y-5">
                    <div>
                        <label htmlFor="email-address" className="block text-sm font-semibold text-secondary/80 mb-2">
                            Email address
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                                <Mail className="h-5 w-5" />
                            </div>
                            <input
                                id="email-address"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-4 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                                placeholder="you@company.com"
                                value={email}
                                onChange={(e) => { setEmail(e.target.value); setEmailError(""); }}
                            />
                        </div>
                        {emailError && (
                            <p className="mt-1.5 text-xs font-medium text-danger flex items-center gap-1">
                                <span className="inline-block h-1 w-1 rounded-full bg-danger" />
                                {emailError}
                            </p>
                        )}
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label htmlFor="password" className="block text-sm font-semibold text-secondary/80">
                                Password
                            </label>
                            <Link href="/forgot-password" className="text-sm font-semibold text-secondary hover:text-primary transition-colors">
                                Forgot password?
                            </Link>
                        </div>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                                <Lock className="h-5 w-5" />
                            </div>
                            <input
                                id="password"
                                name="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="current-password"
                                required
                                onCopy={(e) => e.preventDefault()}
                                onPaste={(e) => e.preventDefault()}
                                className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-11 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((prev) => !prev)}
                                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-secondary/60 hover:text-primary transition-colors"
                                aria-label={showPassword ? "Hide password" : "Show password"}
                                tabIndex={-1}
                            >
                                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="text-danger text-sm font-medium bg-danger-soft px-4 py-3 rounded-lg border border-danger-border flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {error}
                    </div>
                )}

                <div>
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="group relative flex w-full justify-center items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-3.5 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from focus:outline-none focus:ring-4 focus:ring-[var(--ring)] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
                    >
                        <span className="pointer-events-none absolute inset-0 -translate-x-[120%] bg-gradient-to-r from-transparent via-white/25 to-transparent skew-x-[-20deg] group-hover:animate-[auth-shine_1.1s_ease-in-out]"></span>
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Signing in...
                            </>
                        ) : (
                            "Sign in to Dashboard"
                        )}
                    </button>
                </div>
            </form>
        </AuthShell>
    );
}