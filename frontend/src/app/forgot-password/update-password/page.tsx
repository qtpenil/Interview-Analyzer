"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Lock, Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { authApi } from "@/services/authApi";
import { extractApiError } from "@/services/apiClient";
import AuthShell from "@/components/auth/AuthShell";
import { validatePassword } from "@/lib/validators";

export default function UpdatePasswordPage() {
    const router = useRouter();
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const [error, setError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [isResetSuccess, setIsResetSuccess] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleUpdatePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        const trimmedNewPassword = newPassword.trim();
        const trimmedConfirmPassword = confirmPassword.trim();

        const passwordError = validatePassword(trimmedNewPassword);
        if (passwordError) {
            setError(passwordError);
            return;
        }

        if (trimmedNewPassword !== trimmedConfirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setIsSubmitting(true);

        try {
            const res = await authApi.updatePassword({ 
                new_password: trimmedNewPassword, 
                confirm_password: trimmedConfirmPassword 
            });
            setSuccessMessage(res.message || "Password has been successfully updated.");
            setIsResetSuccess(true);
            
            // Redirect to login after a brief delay
            setTimeout(() => {
                router.push("/login");
            }, 3000);
        } catch (err) {
            setError(
                extractApiError(err) ||
                "Failed to update password. Your verification session may have expired."
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AuthShell
            heading="Set a new password."
            description="Create a strong, unique password to secure your account and access the dashboard."
        >
            <div>
                <h2 className="text-center text-3xl font-extrabold tracking-tight text-primary">
                    Update Password
                </h2>
                <p className="mt-2 text-center text-sm text-secondary/50">
                    Remembered your password?{" "}
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

            <form className="mt-8 space-y-6" onSubmit={handleUpdatePassword}>
                <div className="space-y-5">
                    <div>
                        <label htmlFor="new-password" className="block text-sm font-semibold text-secondary/80 mb-2">
                            New Password
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                                <Lock className="h-5 w-5" />
                            </div>
                            <input
                                id="new-password"
                                name="new-password"
                                type={showPassword ? "text" : "password"}
                                required
                                onCopy={(e) => e.preventDefault()}
                                onPaste={(e) => e.preventDefault()}
                                className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-12 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                                placeholder="••••••••"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                            />
                            <button
                                type="button"
                                aria-label={showPassword ? "Hide password" : "Show password"}
                                className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary/50 hover:text-primary transition-colors focus:outline-none"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label htmlFor="confirm-password" className="block text-sm font-semibold text-secondary/80 mb-2">
                            Confirm New Password
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary/60">
                                <Lock className="h-5 w-5" />
                            </div>
                            <input
                                id="confirm-password"
                                name="confirm-password"
                                type={showConfirmPassword ? "text" : "password"}
                                required
                                onCopy={(e) => e.preventDefault()}
                                onPaste={(e) => e.preventDefault()}
                                className="block w-full rounded-xl border border-input-border bg-input-bg py-3 pl-11 pr-12 text-input-text outline-none transition-all placeholder:text-input-placeholder focus:bg-surface-hover/40 focus:border-accent focus:ring-4 focus:ring-[var(--ring)] sm:text-sm"
                                placeholder="••••••••"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                            <button
                                type="button"
                                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                                className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary/50 hover:text-primary transition-colors focus:outline-none"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            >
                                {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
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
                        disabled={isSubmitting || isResetSuccess}
                        className="group relative flex w-full justify-center items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-btn-primary-from to-btn-primary-to px-4 py-3.5 text-sm font-bold text-btn-primary-text shadow-[0_0_20px_-2px_var(--shadow-glow)] hover:shadow-[0_0_30px_-2px_var(--shadow-glow)] hover:from-btn-primary-to hover:to-btn-primary-from focus:outline-none focus:ring-4 focus:ring-[var(--ring)] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
                    >
                        <span className="pointer-events-none absolute inset-0 -translate-x-[120%] bg-gradient-to-r from-transparent via-white/25 to-transparent skew-x-[-20deg] group-hover:animate-[auth-shine_1.1s_ease-in-out]"></span>
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Updating Password...
                            </>
                        ) : (
                            "Update Password"
                        )}
                    </button>
                </div>
            </form>
        </AuthShell>
    );
}
