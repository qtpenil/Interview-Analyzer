const PASSWORD_RESET_EMAIL_KEY = "password_reset_email";

export function getPasswordResetEmail(): string | null {
    if (typeof window === "undefined") {
        return null;
    }
    return sessionStorage.getItem(PASSWORD_RESET_EMAIL_KEY);
}

export function setPasswordResetEmail(email: string): void {
    if (typeof window === "undefined") {
        return;
    }
    sessionStorage.setItem(PASSWORD_RESET_EMAIL_KEY, email);
}

export function clearPasswordResetEmail(): void {
    if (typeof window === "undefined") {
        return;
    }
    sessionStorage.removeItem(PASSWORD_RESET_EMAIL_KEY);
}