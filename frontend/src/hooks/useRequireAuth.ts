"use client";

import { useAuth } from "@/context/AuthContext";

type AuthStatus = "checking" | "authed" | "unauthed";

// Thin wrapper around AuthContext — single source of truth for auth state.
// AuthContext verifies the session on protected routes; this hook just
// reflects its loading/authenticated state without triggering extra requests.
export function useRequireAuth(): AuthStatus {
    const { isLoading, isLoggedIn } = useAuth();

    if (isLoading) return "checking";
    return isLoggedIn ? "authed" : "unauthed";
}
