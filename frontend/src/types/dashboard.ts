export interface QuestionBrief {
  id: string | null;
  question: string | null;
  average_score: string | null;
  feedback: string | null;
}

export interface TopicStat {
  topic: string;
  average_score: string | null;
  highest_score: string | null;
  lowest_score: string | null;
  interview_count: number;
  last_assessed_at: string | null;
  best_feedback: string | null;
  highest_scored_question: QuestionBrief | null;
  lowest_scored_question: QuestionBrief | null;
}

export interface StrongestWeakestTopic {
  topic: string;
  average_score: string | null;
}

export interface BestInterviewTopicInfo {
  topic: string;
  average_score: string | null;
}

export interface BestInterview {
  interview_id: string | null;
  overall_score: string | null;
  title: string;
  highest_scored_topic: BestInterviewTopicInfo | null;
  lowest_scored_topic: BestInterviewTopicInfo | null;
}

export interface DashboardOverview {
  topics: TopicStat[];
  strongest_topic: StrongestWeakestTopic | null;
  weakest_topic: StrongestWeakestTopic | null;
  best_interview: BestInterview | null;
}

export interface TopicQuestionItem {
  id: string | null;
  question_number: number;
  question: string;
  answer: string;
  average_score: string | null;
  difficulty: string | null;
  strong_concepts: string[];
  weak_concepts: string[];
  feedback: string | null;
}

export interface TopicQuestionsResponse {
  total: number;
  limit: number;
  offset: number;
  questions: TopicQuestionItem[];
}

export interface TopicQuestionsParams {
  limit?: number;
  offset?: number;
  sort?: "recent" | "score";
}
