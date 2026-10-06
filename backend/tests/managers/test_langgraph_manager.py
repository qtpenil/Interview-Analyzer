from unittest.mock import MagicMock, patch

import pytest


class TestInterviewGraphRunner:
    def test_runner_initialized(self):
        from app.integration.langGraph.interviewGraph import interview_graph_runner

        assert interview_graph_runner is not None

    def test_extract_segments(self):
        from app.integration.langGraph.interviewGraph import InterviewGraphRunner

        runner = InterviewGraphRunner()
        transcript = [
            {"start": 0.0, "end": 5.0, "text": "Hello"},
            {"start": 5.0, "end": 10.0, "text": "World"},
        ]
        segments = runner._extract_segments(transcript)
        assert len(segments) == 2
        assert segments[0]["start"] == 0.0
        assert segments[1]["end"] == 10.0

    def test_extract_segments_empty(self):
        from app.integration.langGraph.interviewGraph import InterviewGraphRunner

        runner = InterviewGraphRunner()
        segments = runner._extract_segments(None)
        assert segments == []

    def test_format_output_contains_required_keys(self):
        from app.integration.langGraph.interviewGraph import InterviewGraphRunner

        runner = InterviewGraphRunner()
        state = {
            "candidate_metadata": {"candidate_name": "John"},
            "question_answers": [],
            "question_evaluations": [],
            "topics": [],
            "interview_summary": {"hiring_decision": "HIRE", "final_feedback": "Good"},
            "hiring_decision": "HIRE",
            "overall_score": 8.0,
            "technical_score": 7.0,
            "communication_score": 8.0,
            "confidence_score": 9.0,
            "knowledge_depth": 7.5,
            "experience_alignment_score": 7.0,
            "segments": [],
            "blocks": [],
        }
        result = runner._format_output(state)
        assert "candidate_name" in result
        assert "hiring_decision" in result
        assert "overall_score" in result

    def test_to_plain_serializes_nested_objects(self):
        from app.integration.langGraph.interviewGraph import InterviewGraphRunner

        runner = InterviewGraphRunner()

        class CustomObj:
            def __init__(self):
                self.value = "test"

        result = runner._to_plain({"key": CustomObj()})
        assert isinstance(result["key"], str)


class TestProviderStrategy:
    def test_google_provider_builds_model_with_first_pool_key(self):
        with patch("app.core.config.settings.GEMINI_API_KEYS", "key1,key2,key3"):
            with patch("app.integration.langGraph.provider_strategy.ChatGoogleGenerativeAI") as mock_model_cls:
                from app.integration.langGraph.provider_strategy import ProviderManager

                provider = ProviderManager().get_provider("google")
                provider.build_model()
                _, kwargs = mock_model_cls.call_args
                assert kwargs["api_key"] == "key1"
