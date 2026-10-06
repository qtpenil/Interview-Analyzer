import { apiClient } from "./apiClient";
import { ApiMeta, EMPTY_META } from "@/types/api";

import {
    UploadResponse,
    StatusResponse,
    InterviewCancelResponse,
    InterviewListItem,
    InterviewDetail,
    ConceptRef,
} from "@/types/interview";

export interface InterviewListResult {
    items: InterviewListItem[];
    meta: ApiMeta;
}

interface BackendInterviewListItem {
    id: string;
    title: string | null;
    status: "UPLOADED" | "PROCESSING" | "TRANSCRIBING" | "ANALYZING" | "COMPLETED" | "FAILED" | "CANCELLED";
    hiring_decision: "STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE" | null;
    overall_score: number | string | null;
    claimed_experience_years: number | string | null;
    created_at: string;
    failure_reason?: string | null;
    reason?: string | null;
}

interface BackendInterviewTopic {
    topic: string;
    average_score: number | string | null;
    confidence_score: number | string | null;
    strongest_concepts?: (string | ConceptRef)[];
    weakest_concepts?: (string | ConceptRef)[];
    feedback?: string;
    questions?: BackendInterviewQuestion[];
}

interface BackendInterviewQuestion {
    id?: string;
    question_id?: string;
    question: string;
    answer: string;
    accuracy_score?: number | string | null;
    score?: number | string | null;
    average_score?: number | string | null;
    question_number?: number;
    difficulty?: string | null;
    strong_concepts?: string[];
    weak_concepts?: string[];
    feedback?: string;
    category?: string;
}

interface BackendInterviewDetail {
    id: string;
    title: string | null;
    status: "UPLOADED" | "PROCESSING" | "TRANSCRIBING" | "ANALYZING" | "COMPLETED" | "FAILED" | "CANCELLED";
    hiring_decision: "STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE" | null;
    claimed_experience_years: number | string | null;
    overall_score: number | string | null;
    technical_score?: number | string | null;
    communication_score?: number | string | null;
    confidence_score?: number | string | null;
    knowledge_depth?: number | string | null;
    experience_alignment_score?: number | string | null;
    created_at: string;
    topics?: BackendInterviewTopic[];
    summary?: string;
    strengths?: string[];
    weaknesses?: string[];
    risk_factors?: string[];
    questions?: BackendInterviewQuestion[];
    failure_reason?: string | null;
    reason?: string | null;
}

interface BackendInterviewListResponse {
    items: BackendInterviewListItem[];
}


export const uploadInterview = async (
    file: File,
    claimedExperienceYears?: string,
    signal?: AbortSignal,
    onUploadProgress?: (progress: number) => void
): Promise<UploadResponse> => {
    const formData = new FormData();

    formData.append("file", file);

    const trimmedExperience = claimedExperienceYears?.trim();
    if (trimmedExperience) {
        formData.append("claimed_experience_years", trimmedExperience);
    }

    let lastProgress = 0;

    const response =
        await apiClient.post<UploadResponse>(
            `/interviews/upload`,
            formData,
            {
                signal,
                onUploadProgress: (progressEvent) => {
                    if (!progressEvent.total) return;
                    const pct = Math.round(
                        (progressEvent.loaded / progressEvent.total) * 100
                    );
                    // Ensure progress is monotonic — never decrease.
                    // This prevents visual glitches on large files where axios
                    // may report lower loaded values due to chunked encoding/retries.
                    const clamped = Math.min(100, Math.max(0, pct));
                    if (clamped > lastProgress) {
                        lastProgress = clamped;
                        onUploadProgress?.(lastProgress);
                    }
                },
            }
        );

    return response.data;
};

export const getInterviewStatus =
    async (
        interviewId: string
    ): Promise<StatusResponse> => {
        const url = `/interviews/${interviewId}/status`;
        console.log("[getInterviewStatus] interviewId:", JSON.stringify(interviewId), "| url:", url);

        if (!interviewId || !/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(interviewId)) {
            console.warn("[getInterviewStatus] interviewId is NOT a valid UUID — backend will reject it with 'badly formed hexadecimal UUID string'. Check what /interviews/upload returned.");
        }

        const response =
            await apiClient.get<StatusResponse>(url);

        return response.data;
    };

export const getInterviews = async (
    pageSize: number = 100
): Promise<InterviewListResult> => {
    try {
        const response = await apiClient.get<BackendInterviewListResponse>(
            `/interviews/list`,
            {
                params: {
                    page_size: pageSize
                }
            }
        );
        
        const items = (response.data.items || []).map((item: BackendInterviewListItem) => ({
            id: item.id,
            title: item.title,
            status: item.status,
            hiring_decision: item.hiring_decision,
            overall_score: item.overall_score !== null && item.overall_score !== undefined ? String(item.overall_score) : null,
            claimed_experience_years: item.claimed_experience_years !== null && item.claimed_experience_years !== undefined ? String(item.claimed_experience_years) : null,
            created_at: item.created_at,
            failure_reason: item.failure_reason ?? null,
            reason: item.reason ?? null,
        }));

        return { items, meta: response.meta ?? EMPTY_META };
    } catch (error) {
        console.error("Failed to fetch interviews list:", error);
        throw error;
    }
};

const normalizeConcept = (entry: any): ConceptRef => {
    if (typeof entry === "string") return { concept: entry, question_ids: [] };
    if (entry && typeof entry === "object") {
        return {
            concept: entry.concept || entry.name || "",
            question_ids: Array.isArray(entry.question_ids) ? entry.question_ids.map(String) : [],
        };
    }
    return { concept: String(entry), question_ids: [] };
};

const mapConcepts = (value?: (string | ConceptRef)[]): ConceptRef[] =>
    (value || []).map(normalizeConcept);

const mapEmbeddedQuestion = (q: BackendInterviewQuestion, category: string) => ({
    id: q.question_id || q.id || "",
    question: q.question,
    answer: q.answer,
    score:
        q.average_score !== undefined && q.average_score !== null
            ? String(q.average_score)
            : q.accuracy_score !== undefined && q.accuracy_score !== null
              ? String(q.accuracy_score)
              : q.score !== undefined && q.score !== null
                ? String(q.score)
                : "0",
    feedback: q.feedback || "",
    category,
    question_number: q.question_number,
    difficulty: q.difficulty ?? null,
    strong_concepts: q.strong_concepts || [],
    weak_concepts: q.weak_concepts || [],
});

export const getInterviewDetail = async (
    interviewId: string
): Promise<InterviewDetail | null> => {
    try {
        const response = await apiClient.get<BackendInterviewDetail>(
            `/interviews/${interviewId}`
        );
        const data = response.data;

        const embeddedQuestions = (data.topics || []).flatMap((topic) =>
            (topic.questions || []).map((q) => mapEmbeddedQuestion(q, topic.topic))
        );

        const legacyQuestions = (data.questions || []).map((q) => ({
            id: q.question_id || q.id || "",
            question: q.question,
            answer: q.answer,
            score: q.accuracy_score !== undefined && q.accuracy_score !== null ? String(q.accuracy_score) : (q.score !== undefined && q.score !== null ? String(q.score) : "0"),
            feedback: q.feedback || "",
            category: q.category || "",
        }));

        return {
            id: data.id,
            title: data.title,
            status: data.status,
            hiring_decision: data.hiring_decision,
            claimed_experience_years: data.claimed_experience_years !== null && data.claimed_experience_years !== undefined ? String(data.claimed_experience_years) : null,
            overall_score: data.overall_score !== null && data.overall_score !== undefined ? String(data.overall_score) : null,
            technical_score: data.technical_score !== null && data.technical_score !== undefined ? String(data.technical_score) : null,
            communication_score: data.communication_score !== null && data.communication_score !== undefined ? String(data.communication_score) : null,
            confidence_score: data.confidence_score !== null && data.confidence_score !== undefined ? String(data.confidence_score) : null,
            knowledge_depth: data.knowledge_depth !== null && data.knowledge_depth !== undefined ? String(data.knowledge_depth) : null,
            experience_alignment_score: data.experience_alignment_score !== null && data.experience_alignment_score !== undefined ? String(data.experience_alignment_score) : null,
            created_at: data.created_at,
            topics: (data.topics || []).map((topic: BackendInterviewTopic) => {
                const topicEmbedded = (topic.questions || []).map((q) => mapEmbeddedQuestion(q, topic.topic));
                const topicFromGlobal = (data.questions || [])
                    .filter((q) => (q.category || "").trim().toLowerCase() === (topic.topic || "").trim().toLowerCase())
                    .map((q) => mapEmbeddedQuestion(q, topic.topic));
                const finalTopicQuestions = topicEmbedded.length > 0 ? topicEmbedded : topicFromGlobal;

                return {
                    topic: topic.topic,
                    average_score: topic.average_score !== null && topic.average_score !== undefined ? String(topic.average_score) : "0",
                    confidence_score: topic.confidence_score !== null && topic.confidence_score !== undefined ? String(topic.confidence_score) : "0",
                    strongest_concepts: mapConcepts(topic.strongest_concepts),
                    weakest_concepts: mapConcepts(topic.weakest_concepts),
                    feedback: topic.feedback || "",
                    questions: finalTopicQuestions,
                };
            }),
            summary: data.summary || "",
            strengths: data.strengths || [],
            weaknesses: data.weaknesses || [],
            risk_factors: data.risk_factors || [],
            questions: embeddedQuestions.length > 0 ? embeddedQuestions : legacyQuestions,
            failure_reason: data.failure_reason ?? null,
            reason: data.reason ?? null,
        };
    } catch (error) {
        console.error(`Failed to fetch interview detail for ${interviewId}:`, error);
        return null;
    }
};

export const downloadReport = async (interviewId: string): Promise<void> => {
    try {
        const response = await apiClient.get(`/interviews/${interviewId}/report`, {
            responseType: 'blob'
        });
        
        // Create a blob from the response data
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        
        // Prefer the filename the backend set in Content-Disposition
        // (e.g. interview-report-{username}.pdf). Fall back to the interview id.
        let filename = `interview-report-${interviewId}.pdf`;
        const cd = response.headers?.['content-disposition'];
        const match = cd && /filename="?([^"]+)"?/.exec(cd);
        if (match && match[1]) {
            filename = decodeURIComponent(match[1]);
        }
        
        // Create a temporary anchor element and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error(`Failed to download report for ${interviewId}:`, error);
        throw error;
    }
};

export const cancelInterview = async (
    interviewId: string
): Promise<InterviewCancelResponse> => {
    const response =
        await apiClient.post<InterviewCancelResponse>(
            `/interviews/${interviewId}/cancel`
        );

    return response.data;
};
