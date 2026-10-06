export function validatePassword(password: string): string | null {
    if (/\s/.test(password)) {
        return "Password must not contain blank spaces";
    }

    const pattern = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*?])/;

    if (!pattern.test(password)) {
        return "Password must contain 1 uppercase letter, 1 lowercase letter, 1 digit and 1 special character";
    }

    if (password.length < 8) {
        return "Password must be at least 8 characters long";
    }

    return null;
}

export function validateName(name: string): string | null {
    const trimmed = name.trim();
    if (trimmed.length < 3 || trimmed.length > 50) {
        return "Name must be between 3 and 50 characters";
    }
    return null;
}

export function validateEmail(email: string): string | null {
    if (!email.trim()) {
        return "Email is required";
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
        return "Please enter a valid email address";
    }
    return null;
}

export function validateRequired(value: string, fieldName: string): string | null {
    if (!value.trim()) {
        return `${fieldName} is required`;
    }
    return null;
}
