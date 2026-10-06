"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Loader2, KeyRound, CheckCircle2, RefreshCw, ArrowLeft } from "lucide-react";
import { authApi } from "@/services/authApi";
import { extractApiError } from "@/services/apiClient";
import AuthShell from "@/components/auth/AuthShell";
import { getPasswordResetEmail, clearPasswordResetEmail } from "@/lib/passwordReset";

function VerifyOtpForm() {
    const router = useRouter();
    const email = getPasswordResetEmail() || "";

    const [otpCode, setOtpCode] = useState("");
    const [error, setError] = useState("");
    const [otpError, setOtpError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);
    const [isResending, setIsResending] = useState(false);
    const [resendSuccess, setResendSuccess] = useState("");
    const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        if (!email) {
            router.replace("/forgot-password");
        }
    }, [email, router]);

    useEffect(() => {
        if (resendCooldown > 0 && !cooldownRef.current) {
            cooldownRef.current = setInterval(() => {
                setResendCooldown((prev) => {
                    if (prev <= 1) {
                        if (cooldownRef.current) {
                            clearInterval(cooldownRef.current);
                            cooldownRef.current = null;
                        }
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        if (resendCooldown === 0 && cooldownRef.current) {
            clearInterval(cooldownRef.current);
            cooldownRef.current = null;
        }
        return () => {
            if (cooldownRef.current) {
                clearInterval(cooldownRef.current);
                cooldownRef.current = null;
            }
        };
    }, [resendCooldown]);

    const handleResendOtp = async () => {
        setError("");
        setOtpError("");
        setResendSuccess("");
        setIsResending(true);
        try {
            await authApi.forgotPassword({ email });
            setResendSuccess("A new OTP has been sent to your email");
            setResendCooldown(30);
        } catch (err) {
            setError(extractApiError(err));
        } finally {
            setIsResending(false);
        }
    };

    const handleVerifyOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setOtpError("");
        setSuccessMessage("");

        const trimmedOtp = otpCode.trim();
        if (!trimmedOtp) {
            setOtpError("OTP is required");
            return;
        }
        if (trimmedOtp.length !== 6) {
            setOtpError("OTP must be 6 digits");
            return;
        }
        setIsSubmitting(true);

        try {
            const res = await authApi.verifyOtp({ email, otp: otpCode });
            setSuccessMessage(res.message || "OTP verified successfully");

            // Redirect to update-password page after a brief delay
            clearPasswordResetEmail();
            setTimeout(() => {
                router.push("/forgot-password/update-password");
            }, 1500);
        } catch (err) {
            setError(extractApiError(err));
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleBackToEmail = () => {
        // Keep the stored email so the forgot-password page context is
        // preserved; the user simply re-enters/corrects their address there.
        router.push("/forgot-password");
    };

    return (
        <>
            <div>
                <div className="relative flex items-center justify-center">
                    <button
                        type="button"
                        onClick={handleBackToEmail}
                        aria-label="Go back"
                        title="Wrong email? Go back"
                        className="absolute left-0 flex h-9 w-9 items-center justify-center rounded-full border border-default bg-surface/40 text-secondary shadow-sm transition hover:border-accent-soft-border hover:bg-accent-soft hover:text-primary"
                    >
                        <ArrowLeft className="h-4 w-4" />
                    </button>
                    <h2 className="text-center text-3xl font-extrabold tracking-tight text-primary">
                        Verify OTP
                    </h2>
                </div>
                <p className="mt-2 text-center text-sm text-secondary/50">
                    Enter the code sent to <span className="font-semibold text-secondary">{email}</span>
                </p>
            </div>

            {successMessage && (
                <div className="mt-6 text-secondary text-sm font-medium bg-accent-soft px-4 py-3 rounded-lg border border-accent-soft-border flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-secondary" />
                    {successMessage}
                </div>
            )}

            <form className="mt-8 space-y-6" onSubmit={handleVerifyOtp}>
                <div className="space-y-5">
                    <div>
                        <label htmlFor="otp" className="block text-sm font-semibold text-secondary/80 mb-2">
                            OTP Code
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                                <KeyRound className="h-5 w-5" />
                            </div>
                            <input
                                id="otp"
                                name="otp"
                                type="text"
                                required
                                className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-4 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm tracking-widest font-mono"
                                placeholder="123456"
                                maxLength={6}
                                value={otpCode}
                                onChange={(e) => { setOtpCode(e.target.value); setOtpError(""); }}
                            />
                        </div>
                        {otpError && (
                            <p className="mt-1.5 text-xs font-medium text-danger flex items-center gap-1">
                                <span className="inline-block h-1 w-1 rounded-full bg-danger" />
                                {otpError}
                            </p>
                        )}
                        <p className="mt-2 text-sm text-muted">
                            Enter the 6-digit verification code sent to your email.
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
                                Verifying OTP...
                            </>
                        ) : (
                            "Verify OTP"
                        )}
                    </button>

                    {resendSuccess && (
                        <p className="mt-3 text-xs font-medium text-secondary bg-accent-soft px-3 py-2 rounded-lg border border-accent-soft-border flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                            {resendSuccess}
                        </p>
                    )}

                    <div className="mt-4 text-center">
                        <button
                            type="button"
                            onClick={handleResendOtp}
                            disabled={resendCooldown > 0 || isResending}
                            className="inline-flex items-center gap-1.5 text-sm font-semibold text-secondary hover:text-primary transition-colors disabled:text-muted disabled:cursor-not-allowed"
                        >
                            <RefreshCw className={`h-4 w-4 ${isResending ? "animate-spin" : ""}`} />
                            {isResending
                                ? "Sending..."
                                : resendCooldown > 0
                                    ? `Resend OTP in ${resendCooldown}s`
                                    : "Resend OTP"}
                        </button>
                    </div>
                </div>
            </form>
        </>
    );
}

export default function VerifyOtpPage() {
    return (
        <AuthShell
            heading="Verify your identity."
            description="Enter the one-time passcode sent to your inbox to securely advance to setting your new password."
        >
            <VerifyOtpForm />
        </AuthShell>
    );
}
