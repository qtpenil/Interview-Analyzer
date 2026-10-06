from unittest.mock import patch

import pytest

from app.integration.langGraph.security_hardening import preprocess_transcript


class TestPreprocessTranscript:
    def test_normal_transcript_unchanged(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello, welcome to the interview."},
        ]
        result = preprocess_transcript(segments, "interview-1")
        assert result == segments

    def test_email_redaction_enabled(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "My email is john.doe@example.com"},
        ]
        with patch("app.core.config.settings.ENABLE_PII_REDACTION", True):
            result = preprocess_transcript(segments, "interview-1")
            assert "john.doe@example.com" not in result[0]["text"]
            assert "[EMAIL]" in result[0]["text"]

    def test_phone_redaction_enabled(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Call me at +1-555-123-4567"},
        ]
        with patch("app.core.config.settings.ENABLE_PII_REDACTION", True):
            result = preprocess_transcript(segments, "interview-1")
            assert "555" not in result[0]["text"]
            assert "[PHONE]" in result[0]["text"]

    def test_pii_redaction_disabled(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Email: test@example.com"},
        ]
        with patch("app.core.config.settings.ENABLE_PII_REDACTION", False):
            result = preprocess_transcript(segments, "interview-1")
            assert "test@example.com" in result[0]["text"]

    def test_empty_segments(self):
        result = preprocess_transcript([], "interview-1")
        assert result == []

    def test_unicode_normalization(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Caf\u00e9 r\u00e9sum\u00e9"},
        ]
        result = preprocess_transcript(segments, "interview-1")
        assert result[0]["text"] == "Caf\u00e9 r\u00e9sum\u00e9"
