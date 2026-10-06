import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiMeta } from '@/types/api';

// Expose the envelope's `meta` on every Axios response (it's otherwise
// discarded when we unwrap `data` below). Optional, so existing callers
// that don't read it are unaffected.
declare module 'axios' {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    export interface AxiosResponse<T = any> {
        meta?: ApiMeta | null;
    }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Separate instance for refresh calls to avoid interceptor recursion
export const refreshClient = axios.create({
    baseURL: BASE_URL,
    withCredentials: true,
});

export const apiClient = axios.create({
    baseURL: BASE_URL,
    withCredentials: true,
});

/**
 * IMPORTANT: This backend authenticates purely via httpOnly cookies
 * (see get_current_user, which only ever reads request.cookies["access_token"]).
 * It never inspects an Authorization header. Because the cookies are httpOnly,
 * frontend JS cannot read or write their values (Cookies.get/set on
 * "access_token"/"refresh_token" will not work) — and it doesn't need to,
 * since withCredentials: true makes the browser attach them automatically.
 *
 * So: no request interceptor is needed to attach a header. The only job left
 * for the response interceptor is to catch a 401, hit /auth/refreshToken
 * (which reads the refresh cookie and sets a new access-token cookie itself),
 * and retry the original request — the new cookie goes along for free.
 */

let isRefreshing = false;
let failedQueue: Array<{ resolve: () => void; reject: (error: any) => void }> = [];

const processQueue = (error: any) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve();
        }
    });
    failedQueue = [];
};

apiClient.interceptors.response.use(
    (response) => {
        // Backend wraps all responses in a { success, message, data, meta } envelope.
        // Unwrap it so callers receive the actual payload (e.g. response.data.data.interview_id
        // becomes response.data.interview_id). Skip blobs (file downloads) and
        // message-only responses (SuccessResponse with data: null — e.g. OTP
        // endpoints), where unwrapping would null out response.data entirely.
        const payload = response.data;
        if (
            response.config.responseType !== 'blob' &&
            payload &&
            typeof payload === 'object' &&
            'success' in payload &&
            'data' in payload &&
            payload.data !== null
        ) {
            response.data = payload.data;
            response.meta = (payload as { meta?: ApiMeta | null }).meta ?? null;
        }
        return response;
    },
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
            if (isRefreshing) {
                // Another request already triggered a refresh — wait for it, then retry
                return new Promise<void>((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then(() => apiClient(originalRequest))
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Refresh token is read from its own httpOnly cookie server-side.
                // New access_token cookie is set via Set-Cookie on this response.
                await refreshClient.post('/auth/refreshToken');

                processQueue(null);
                isRefreshing = false;

                // Retry original request — new access_token cookie is sent automatically
                return apiClient(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError);
                isRefreshing = false;

                if (typeof window !== 'undefined') {
                    localStorage.removeItem('session_hint');
                    window.location.href = '/login';
                }
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

/**
 * Extract a human-readable message from a rejected request.
 * Handles both the app's envelope ({ success:false, message }) and
 * FastAPI's default validation error ({ detail }) used on 422s.
 */
export const extractApiError = (error: unknown): string => {
    const err = error as AxiosError<Record<string, unknown>>;
    const data = err?.response?.data;

    if (data && typeof data === 'object') {
        const message = data.message;
        if (typeof message === 'string' && message.length > 0) return message;

        const detail = data.detail;
        if (typeof detail === 'string' && detail.length > 0) return detail;
        if (Array.isArray(detail)) {
            return detail
                .map((d: any) => (typeof d?.msg === 'string' ? d.msg : JSON.stringify(d)))
                .join('; ');
        }
    }

    if (err?.message) return err.message;
    return 'Something went wrong. Please try again.';
};