"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Mail, Lock, ShieldCheck, User, Eye, EyeOff } from "lucide-react";
import AuthShell from "@/components/auth/AuthShell";
import { validatePassword, validateName, validateEmail } from "@/lib/validators";

export default function RegisterPage() {
    const router = useRouter();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState("");
    const [nameError, setNameError] = useState("");
    const [emailError, setEmailError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { register, isLoggedIn, isLoading } = useAuth();

    useEffect(() => {
        if (!isLoading && isLoggedIn) {
            router.push("/dashboard");
        }
    }, [isLoggedIn, isLoading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setNameError("");
        setEmailError("");

        const trimmedName = name.trim();
        const trimmedEmail = email.trim();
        const trimmedPassword = password.trim();
        const trimmedConfirmPassword = confirmPassword.trim();

        const nameErrorMsg = validateName(trimmedName);
        if (nameErrorMsg) {
            setNameError(nameErrorMsg);
            return;
        }

        const emailErrorMsg = validateEmail(trimmedEmail);
        if (emailErrorMsg) {
            setEmailError(emailErrorMsg);
            return;
        }

        const passwordError = validatePassword(trimmedPassword);
        if (passwordError) {
            setError(passwordError);
            return;
        }

        if (trimmedPassword !== trimmedConfirmPassword.trim()) {
            setError("Passwords do not match");
            return;
        }

        setIsSubmitting(true);

        try {
            await register({ name: trimmedName, email: trimmedEmail, password: trimmedPassword });
        } catch (err: any) {
            setError(err.response?.data?.message || "Failed to register. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthShell
            heading="Join the future of technical hiring."
            description="Create your account today and gain access to unparalleled AI-driven interview analytics and candidate evaluation tools."
            badge={
                <>
                    <ShieldCheck className="h-4 w-4" /> Secure &amp; Confidential
                </>
            }
        >
            <div>
                <h2 className="text-center text-3xl font-extrabold tracking-tight text-primary">
                    Create an account
                </h2>
                <p className="mt-2 text-center text-sm text-secondary/50">
                    Already have an account?{" "}
                    <Link href="/login" className="font-bold text-secondary hover:text-primary transition-colors">
                        Sign in instead
                    </Link>
                </p>
            </div>

            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="fullname" className="block text-sm font-semibold text-secondary/80 mb-2">
                        Full Name
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                            <User className="h-5 w-5" />
                        </div>
                        <input
                            id="fullname"
                            name="fullname"
                            type="text"
                            autoComplete="name"
                            required
                            className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-4 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                            placeholder="John Doe"
                            value={name}
                            onChange={(e) => { setName(e.target.value); setNameError(""); }}
                        />
                    </div>
                    {nameError && (
                        <p className="mt-1.5 text-xs font-medium text-danger flex items-center gap-1">
                            <span className="inline-block h-1 w-1 rounded-full bg-danger" />
                            {nameError}
                        </p>
                    )}
                    {!nameError && (
                        <p className="mt-1.5 text-xs text-muted">No blank spaces allowed · 3–50 characters</p>
                    )}
                </div>

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
                    <label htmlFor="password" className="block text-sm font-semibold text-secondary/80 mb-2">
                        Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                            <Lock className="h-5 w-5" />
                        </div>
                        <input
                            id="password"
                            name="password"
                            type={showPassword ? "text" : "password"}
                            autoComplete="new-password"
                            required
                            onCopy={(e) => e.preventDefault()}
                            onPaste={(e) => e.preventDefault()}
                            className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-11 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                            placeholder="Create a strong password"
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
                    <p className="mt-1.5 text-xs text-muted">No blank spaces allowed</p>
                </div>

                <div>
                    <label htmlFor="confirm-password" className="block text-sm font-semibold text-secondary/80 mb-2">
                        Confirm Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                            <ShieldCheck className="h-5 w-5" />
                        </div>
                        <input
                            id="confirm-password"
                            name="confirm-password"
                            type={showConfirmPassword ? "text" : "password"}
                            autoComplete="new-password"
                            required
                            onCopy={(e) => e.preventDefault()}
                            onPaste={(e) => e.preventDefault()}
                            className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-11 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                            placeholder="Repeat your password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                        <button
                            type="button"
                            onClick={() => setShowConfirmPassword((prev) => !prev)}
                            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-secondary/60 hover:text-primary transition-colors"
                            aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                            tabIndex={-1}
                        >
                            {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
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

                <div className="pt-2">
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="group relative flex w-full justify-center items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-3.5 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from focus:outline-none focus:ring-4 focus:ring-[var(--ring)] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
                    >
                        <span className="pointer-events-none absolute inset-0 -translate-x-[120%] bg-gradient-to-r from-transparent via-white/25 to-transparent skew-x-[-20deg] group-hover:animate-[auth-shine_1.1s_ease-in-out]"></span>
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Creating account...
                            </>
                        ) : (
                            "Create Account"
                        )}
                    </button>
                </div>
            </form>
        </AuthShell>
    );
}
