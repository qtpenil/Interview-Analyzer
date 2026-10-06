"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { LoginRequest, RegisterRequest, User } from "@/types/auth";
import { authApi } from "@/services/authApi";
import { getInterviews } from "@/services/interviewApi";

interface AuthContextType {
    user: User | null;
    isLoggedIn: boolean;
    login: (credentials: LoginRequest) => Promise<void>;
    register: (credentials: RegisterRequest) => Promise<void>;
    logout: () => Promise<void>;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Non-sensitive, JS-readable flag used ONLY to avoid a flash-of-login-page
// on refresh. It carries no auth power — the real auth cookies are httpOnly
// and enforced server-side. If it's stale (e.g. token actually expired),
// apiClient's 401 -> refresh -> redirect flow is what actually protects routes.
const SESSION_HINT_KEY = "session_hint";

const isProtectedRoute = (path: string) =>
    path !== "/" &&
    path !== "/login" &&
    path !== "/register" &&
    !path.startsWith("/forgot-password");

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    // Single source of truth for "logged in". Driven by a real backend
    // session check (httpOnly cookie), NOT by the fragile localStorage hint.
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        let cancelled = false;

        // Optimistically restore the cached user. A present, valid hint means
        // we're logged in — mark authenticated so public pages (landing, etc.)
        // reflect the logged-in state too, not just protected routes.
        const hint = typeof window !== "undefined" ? localStorage.getItem(SESSION_HINT_KEY) : null;
        if (hint) {
            try {
                const parsed = JSON.parse(hint);
                if (parsed && typeof parsed.email === "string") {
                    setUser(parsed as User);
                    setIsAuthenticated(true);
                } else {
                    localStorage.removeItem(SESSION_HINT_KEY);
                }
            } catch {
                localStorage.removeItem(SESSION_HINT_KEY);
            }
        }

        // Verify the real session against the backend using the httpOnly
        // cookie. This is what the sidebar and route guards must agree on,
        // so the sidebar can't disappear while a protected page is visible.
        // Only do this on protected routes — calling it on public routes
        // (e.g. /login) would 401 and the apiClient interceptor's hard
        // redirect to /login would create an infinite reload loop.
        const verify = async () => {
            try {
                await getInterviews(1);
                if (!cancelled) setIsAuthenticated(true);
            } catch {
                if (!cancelled) {
                    localStorage.removeItem(SESSION_HINT_KEY);
                    setUser(null);
                    setIsAuthenticated(false);
                    if (isProtectedRoute(pathname)) router.push("/login");
                }
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        };

        if (isProtectedRoute(pathname)) {
            verify();
        } else {
            setIsLoading(false);
        }

        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const login = async (credentials: LoginRequest) => {
        try {
            const data = await authApi.login(credentials);
            // apiClient's response interceptor already unwraps the
            // { success, message, data } envelope, so `data` is the User object.
            setUser(data);
            localStorage.setItem(SESSION_HINT_KEY, JSON.stringify(data));
            setIsAuthenticated(true);
            router.push("/dashboard");
        } catch (error) {
            console.error("Login failed:", error);
            throw error;
        }
    };

    const register = async (credentials: RegisterRequest) => {
        try {
            await authApi.register(credentials);
            await login({ email: credentials.email, password: credentials.password });
        } catch (error) {
            console.error("Registration failed:", error);
            throw error;
        }
    };

    const logout = async () => {
        try {
            // NOTE: requires adding a POST /auth/logout route on the backend that
            // calls clear_auth_cookie(response, "access") and clear_auth_cookie(response, "refresh").
            // Without it, the httpOnly cookies are never actually cleared server-side.
            await authApi.logout();
        } catch (error) {
            console.error("Logout request failed (clearing local state anyway):", error);
        } finally {
            localStorage.removeItem(SESSION_HINT_KEY);
            setUser(null);
            setIsAuthenticated(false);
            router.push("/login");
        }
    };

    return (
        <AuthContext.Provider
            value={{ user, isLoggedIn: isAuthenticated, login, register, logout, isLoading }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};