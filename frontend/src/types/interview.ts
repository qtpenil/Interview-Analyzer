export interface UploadResponse {
    interview_id: string;
    status: "UPLOADED";
}

export interface StatusResponse {
    interview_id: string;

    status:
        | "UPLOADED"
        | "PROCESSING"
        | "TRANSCRIBING"
        | "ANALYZING"
        | "COMPLETED"
        | "FAILED"
        | "CANCELLED";

    processing_started_at: string | null;

    processing_completed_at: string | null;

    failure_reason?: string | null;

    reason?: string | null;
}

export interface InterviewListItem {
    id: string;
    title: string | null;
    status: "UPLOADED" | "PROCESSING" | "TRANSCRIBING" | "ANALYZING" | "COMPLETED" | "FAILED" | "CANCELLED";
    hiring_decision: "STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE" | null;
    overall_score: string | null;
    claimed_experience_years: string | null;
    created_at: string;
    failure_reason?: string | null;
    reason?: string | null;
}

export interface ConceptRef {
    concept: string;
    question_ids: string[];
}

export interface InterviewTopic {
    topic: string;
    average_score: string;
    confidence_score: string;
    strongest_concepts: ConceptRef[];
    weakest_concepts: ConceptRef[];
    feedback?: string;
    questions?: InterviewQuestion[];
}

export interface InterviewQuestion {
    id: string;
    question: string;
    answer: string;
    score: string;
    feedback: string;
    category: string;
    question_number?: number;
    difficulty?: string | null;
    strong_concepts?: string[];
    weak_concepts?: string[];
}

export interface InterviewCancelResponse {
    interview_id: string;
    status: string;
    message: string;
}

export interface InterviewDetail {
    id: string;
    title: string | null;
    status: "UPLOADED" | "PROCESSING" | "TRANSCRIBING" | "ANALYZING" | "COMPLETED" | "FAILED" | "CANCELLED";
    hiring_decision: "STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE" | null;
    claimed_experience_years: string | null;
    overall_score: string | null;
    technical_score?: string | null;
    communication_score?: string | null;
    confidence_score?: string | null;
    knowledge_depth?: string | null;
    experience_alignment_score?: string | null;
    created_at: string;
    topics: InterviewTopic[];
    summary?: string;
    strengths?: string[];
    weaknesses?: string[];
    risk_factors?: string[];
    questions?: InterviewQuestion[];
    failure_reason?: string | null;
    reason?: string | null;
}