"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Mail, CheckCircle2 } from "lucide-react";
import { authApi } from "@/services/authApi";
import { extractApiError } from "@/services/apiClient";
import AuthShell from "@/components/auth/AuthShell";
import { validateEmail } from "@/lib/validators";
import { setPasswordResetEmail } from "@/lib/passwordReset";

export default function ForgotPasswordPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [emailError, setEmailError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleRequestOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setEmailError("");
        setSuccessMessage("");

        const emailErrorMsg = validateEmail(email);
        if (emailErrorMsg) {
            setEmailError(emailErrorMsg);
            return;
        }
        setIsSubmitting(true);

        try {
            const res = await authApi.forgotPassword({ email });
            setSuccessMessage(res.message || "An OTP has been sent to your email");
            
            // Redirect to verify-otp page after a brief delay
            setPasswordResetEmail(email);
            setTimeout(() => {
                router.push("/forgot-password/verify-otp");
            }, 1500);
        } catch (err) {
            setError(extractApiError(err));
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthShell
            heading="Recover your account access."
            description="Securely reset your password and get back to finding the best candidates with AI-powered insights."
        >
            <div>
                <h2 className="text-center text-3xl font-extrabold tracking-tight text-primary">
                    Forgot Password
                </h2>
                <p className="mt-2 text-center text-sm text-secondary/50">
                    Remember your password?{" "}
                    <Link href="/login" className="font-bold text-secondary hover:text-primary transition-colors">
                        Back to login
                    </Link>
                </p>
            </div>

            {successMessage && (
                <div className="mt-6 text-secondary text-sm font-medium bg-accent-soft px-4 py-3 rounded-lg border border-accent-soft-border flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-secondary" />
                    {successMessage}
                </div>
            )}

            <form className="mt-8 space-y-6" onSubmit={handleRequestOtp}>
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
                        <p className="mt-2 text-sm text-muted">
                            Enter the email associated with your account and we'll send you an OTP to reset your password.
                        </p>
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
                        disabled={isSubmitting || !!successMessage}
                        className="group relative flex w-full justify-center items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-3.5 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from focus:outline-none focus:ring-4 focus:ring-[var(--ring)] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
                    >
                        <span className="pointer-events-none absolute inset-0 -translate-x-[120%] bg-gradient-to-r from-transparent via-white/25 to-transparent skew-x-[-20deg] group-hover:animate-[auth-shine_1.1s_ease-in-out]"></span>
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Sending OTP...
                            </>
                        ) : (
                            "Send OTP"
                        )}
                    </button>
                </div>
            </form>
        </AuthShell>
    );
}