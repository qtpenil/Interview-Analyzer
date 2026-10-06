from unittest.mock import patch

import pytest


class TestClassifyTranscript:
    def test_classifier_returns_interview(self):
        from app.integration.interview_classifier.classifier import classify_transcript

        mock_response = type(
            "Response", (), {"text": '{"is_interview": true, "reason": "QA format detected", "confidence": 0.95}'}
        )()

        with patch("app.integration.interview_classifier.classifier.genai.Client") as mock_client:
            mock_client.return_value.models.generate_content.return_value = mock_response
            with patch("app.integration.interview_classifier.classifier.settings.GEMINI_API_KEYS", "fake-key"):
                result = classify_transcript("Some interview text", "test-1")
                assert result["is_interview"] is True

    def test_classifier_rejects_non_interview(self):
        from app.integration.interview_classifier.classifier import classify_transcript

        mock_response = type(
            "Response", (), {"text": '{"is_interview": false, "reason": "Music only", "confidence": 0.99}'}
        )()

        with patch("app.integration.interview_classifier.classifier.genai.Client") as mock_client:
            mock_client.return_value.models.generate_content.return_value = mock_response
            with patch("app.integration.interview_classifier.classifier.settings.GEMINI_API_KEYS", "fake-key"):
                result = classify_transcript("La la la", "test-2")
                assert result["is_interview"] is False

    def test_classifier_no_api_keys_skips(self):
        from app.integration.interview_classifier.classifier import classify_transcript

        with patch("app.integration.interview_classifier.classifier.settings.GEMINI_API_KEYS", ""):
            result = classify_transcript("Some text", "test-3")
            assert result["is_interview"] is True
            assert "disabled" in result["reason"]

    def test_classifier_all_attempts_fail(self):
        from app.integration.interview_classifier.classifier import classify_transcript

        with patch("app.integration.interview_classifier.classifier.genai.Client") as mock_client:
            mock_client.side_effect = Exception("API error")
            with patch("app.integration.interview_classifier.classifier.settings.GEMINI_API_KEYS", "fake-key"):
                result = classify_transcript("Some text", "test-4")
                assert result["is_interview"] is True
                assert "unavailable" in result["reason"]

    def test_classifier_truncates_long_text(self):
        from app.integration.interview_classifier.classifier import classify_transcript

        long_text = "hello " * 2000

        mock_response = type("Response", (), {"text": '{"is_interview": true, "reason": "test", "confidence": 1.0}'})()

        with patch("app.integration.interview_classifier.classifier.genai.Client") as mock_client:
            mock_client.return_value.models.generate_content.return_value = mock_response
            with patch("app.integration.interview_classifier.classifier.settings.GEMINI_API_KEYS", "fake-key"):
                result = classify_transcript(long_text, "test-5")
                assert result["is_interview"] is True
