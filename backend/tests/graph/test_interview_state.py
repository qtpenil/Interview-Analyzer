from app.integration.langGraph.interviewState import InterviewGraphState


class TestInterviewGraphState:
    def test_state_keys_exist(self):
        required_keys = {
            "interview_id",
            "raw_transcript",
            "conversation_blocks",
            "candidate_name",
            "claimed_experience_years",
            "question_answers",
            "question_evaluations",
            "topic_summaries",
            "interview_summary",
            "current_node",
            "started_at",
            "completed_at",
            "errors",
            "warnings",
        }
        state_keys = set(InterviewGraphState.__annotations__.keys())
        for key in required_keys:
            assert key in state_keys, f"Missing required key: {key}"

    def test_state_has_status_fields(self):
        status_keys = {
            "metadata_extraction_status",
            "transcript_processing_status",
            "assessment_status",
            "topic_aggregation_status",
            "final_summary_status",
        }
        state_keys = set(InterviewGraphState.__annotations__.keys())
        for key in status_keys:
            assert key in state_keys, f"Missing status key: {key}"
