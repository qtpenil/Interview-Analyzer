export interface User {
    name: string;
    email: string;
}

// Matches SuccessResponse(message=..., data=<user>) from authRoutes.py.
// access_token/refresh_token are NEVER in this body — they're set as
// httpOnly cookies directly by the backend (see set_auth_cookie).
export interface AuthResponse {
    message: string;
    data: User;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    name: string;
    email: string;
    password: string;
}

export interface ForgotPasswordRequest {
    email: string;
}

export interface VerifyOtpRequest {
    email: string;
    otp: string;
}

export interface UpdatePasswordRequest {
    new_password: string;
    confirm_password: string;
}

export interface DefaultResponse {
    success: boolean;
    message: string;
}