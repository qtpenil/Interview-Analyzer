import { apiClient } from './apiClient';
import { LoginRequest, RegisterRequest, User, ForgotPasswordRequest, VerifyOtpRequest, UpdatePasswordRequest, DefaultResponse } from '@/types/auth';

export const authApi = {
    login: async (credentials: LoginRequest): Promise<User> => {
        const response = await apiClient.post<User>('/auth/login', credentials);
        return response.data;
    },

    register: async (credentials: RegisterRequest): Promise<User> => {
        const response = await apiClient.post<User>('/auth/register', credentials);
        return response.data;
    },

    // Requires a new backend route: POST /auth/logout, which should call
    // clear_auth_cookie(response, "access") and clear_auth_cookie(response, "refresh")
    // — otherwise the httpOnly cookies never actually get cleared server-side.
    logout: async (): Promise<void> => {
        await apiClient.post('/auth/logout');
    },

    forgotPassword: async (data: ForgotPasswordRequest): Promise<DefaultResponse> => {
        const response = await apiClient.post<DefaultResponse>('/auth/forgot-password', data);
        return response.data;
    },

    verifyOtp: async (data: VerifyOtpRequest): Promise<DefaultResponse> => {
        const response = await apiClient.post<DefaultResponse>('/auth/verify-otp', data);
        return response.data;
    },

    updatePassword: async (data: UpdatePasswordRequest): Promise<DefaultResponse> => {
        const response = await apiClient.post<DefaultResponse>('/auth/update-password', data);
        return response.data;
    },
};