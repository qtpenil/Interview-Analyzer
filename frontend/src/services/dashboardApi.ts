import { apiClient } from "./apiClient";
import type {
  DashboardOverview,
  TopicStat,
  TopicQuestionsResponse,
  TopicQuestionsParams,
  QuestionBrief,
  StrongestWeakestTopic,
  BestInterview,
  BestInterviewTopicInfo,
  TopicQuestionItem,
} from "@/types/dashboard";

interface BackendQuestionBrief {
  id: string | null;
  question: string | null;
  average_score: number | string | null;
  feedback: string | null;
}

interface BackendTopicStat {
  topic: string;
  average_score: number | string | null;
  highest_score: number | string | null;
  lowest_score: number | string | null;
  interview_count: number;
  last_assessed_at: string | null;
  best_feedback: string | null;
  highest_scored_question: BackendQuestionBrief | null;
  lowest_scored_question: BackendQuestionBrief | null;
}

interface BackendStrongestWeakestTopic {
  topic: string;
  average_score: number | string | null;
}

interface BackendBestInterviewTopicInfo {
  topic: string;
  average_score: number | string | null;
}

interface BackendBestInterview {
  interview_id: string | null;
  overall_score: number | string | null;
  title: string;
  highest_scored_topic: BackendBestInterviewTopicInfo | null;
  lowest_scored_topic: BackendBestInterviewTopicInfo | null;
}

interface BackendDashboardOverview {
  topics: BackendTopicStat[];
  strongest_topic: BackendStrongestWeakestTopic | null;
  weakest_topic: BackendStrongestWeakestTopic | null;
  best_interview: BackendBestInterview | null;
}

interface BackendTopicQuestionItem {
  id: string | null;
  question_number: number;
  question: string;
  answer: string;
  average_score: number | string | null;
  difficulty: string | null;
  strong_concepts: string[];
  weak_concepts: string[];
  feedback: string | null;
}

interface BackendTopicQuestionsResponse {
  total: number;
  limit: number;
  offset: number;
  questions: BackendTopicQuestionItem[];
}

const safeStr = (val: number | string | null | undefined): string | null => {
  if (val === null || val === undefined) return null;
  return String(val);
};

const mapQuestionBrief = (
  q: BackendQuestionBrief | null | undefined
): QuestionBrief | null => {
  if (!q) return null;
  return {
    id: q.id ?? null,
    question: q.question ?? null,
    average_score: safeStr(q.average_score),
    feedback: q.feedback ?? null,
  };
};

const mapTopicStat = (ts: BackendTopicStat): TopicStat => ({
  topic: ts.topic,
  average_score: safeStr(ts.average_score),
  highest_score: safeStr(ts.highest_score),
  lowest_score: safeStr(ts.lowest_score),
  interview_count: ts.interview_count ?? 0,
  last_assessed_at: ts.last_assessed_at ?? null,
  best_feedback: ts.best_feedback ?? null,
  highest_scored_question: mapQuestionBrief(ts.highest_scored_question),
  lowest_scored_question: mapQuestionBrief(ts.lowest_scored_question),
});

const mapStrongestWeakest = (
  sw: BackendStrongestWeakestTopic | null | undefined
): StrongestWeakestTopic | null => {
  if (!sw) return null;
  return {
    topic: sw.topic,
    average_score: safeStr(sw.average_score),
  };
};

const mapBestInterviewTopic = (
  t: BackendBestInterviewTopicInfo | null | undefined
): BestInterviewTopicInfo | null => {
  if (!t) return null;
  return {
    topic: t.topic,
    average_score: safeStr(t.average_score),
  };
};

const mapBestInterview = (
  bi: BackendBestInterview | null | undefined
): BestInterview | null => {
  if (!bi) return null;
  return {
    interview_id: bi.interview_id ?? null,
    overall_score: safeStr(bi.overall_score),
    title: bi.title || "Untitled Interview",
    highest_scored_topic: mapBestInterviewTopic(bi.highest_scored_topic),
    lowest_scored_topic: mapBestInterviewTopic(bi.lowest_scored_topic),
  };
};

const mapTopicQuestion = (q: BackendTopicQuestionItem): TopicQuestionItem => ({
  id: q.id ?? null,
  question_number: q.question_number,
  question: q.question,
  answer: q.answer,
  average_score: safeStr(q.average_score),
  difficulty: q.difficulty ?? null,
  strong_concepts: q.strong_concepts || [],
  weak_concepts: q.weak_concepts || [],
  feedback: q.feedback ?? null,
});

export const getDashboardOverview = async (): Promise<DashboardOverview> => {
  try {
    const response = await apiClient.get<BackendDashboardOverview>(
      "/dashboard/overview"
    );
    const data = response.data;

    return {
      topics: (data.topics || []).map(mapTopicStat),
      strongest_topic: mapStrongestWeakest(data.strongest_topic),
      weakest_topic: mapStrongestWeakest(data.weakest_topic),
      best_interview: mapBestInterview(data.best_interview),
    };
  } catch (error) {
    console.error("Failed to fetch dashboard overview:", error);
    throw error;
  }
};

export const getTopicQuestions = async (
  topic: string,
  params?: TopicQuestionsParams
): Promise<TopicQuestionsResponse> => {
  try {
    const response = await apiClient.get<BackendTopicQuestionsResponse>(
      `/dashboard/topics/${encodeURIComponent(topic)}/questions`,
      {
        params: {
          limit: params?.limit ?? 20,
          offset: params?.offset ?? 0,
          sort: params?.sort ?? "recent",
        },
      }
    );
    const data = response.data;

    return {
      total: data.total ?? 0,
      limit: data.limit ?? params?.limit ?? 20,
      offset: data.offset ?? params?.offset ?? 0,
      questions: (data.questions || []).map(mapTopicQuestion),
    };
  } catch (error) {
    console.error(`Failed to fetch questions for topic ${topic}:`, error);
    throw error;
  }
};
