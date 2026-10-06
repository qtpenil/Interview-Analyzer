// Shared types for the backend's response envelope.
//
// Every successful response is shaped like:
// {
//   "success": boolean,         // always true on success
//   "message": string,          // human-readable message
//   "data": <T>,                // the actual payload (shape varies per endpoint)
//   "meta": {                   // optional, usually null
//     "total": number | null,
//     "page": number | null,
//     "page_size": number | null
//   }
// }
//
// NOTE: `src/services/apiClient.ts` unwraps the envelope in a response
// interceptor, so callers receive `response.data` = the payload's `data`
// field (not the full envelope). `meta` is attached to `response.meta`.

export interface ApiMeta {
    total: number | null;
    page: number | null;
    page_size: number | null;
}

export interface ApiEnvelope<T> {
    success: boolean;
    message: string;
    data: T;
    meta?: ApiMeta | null;
}

export const EMPTY_META: ApiMeta = {
    total: null,
    page: null,
    page_size: null,
};
