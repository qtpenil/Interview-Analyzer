from unittest.mock import MagicMock, patch

import pytest


class TestInterviewPDFService:
    def test_generate_pdf_success(self, sample_state_dict: dict):
        from app.integration.pdf.service import interview_pdf_service

        result = interview_pdf_service.generate("test-id", sample_state_dict)
        assert result is not None
        assert hasattr(result, "getbuffer")
        pdf_bytes = result.getvalue()
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_with_minimal_state(self):
        from app.integration.pdf.service import interview_pdf_service

        minimal_state = {
            "interview_id": "test-id",
            "candidate_name": "Test",
            "hiring_decision": "BORDERLINE",
            "overall_score": 5.0,
            "topics": [],
            "questions": [],
            "interview_summary": {},
            "strengths": [],
            "weaknesses": [],
            "risk_factors": [],
        }
        result = interview_pdf_service.generate("test-id", minimal_state)
        pdf_bytes = result.getvalue()
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_empty_state_handled(self):
        from app.integration.pdf.service import interview_pdf_service

        empty_state = {}
        result = interview_pdf_service.generate("test-id", empty_state)
        pdf_bytes = result.getvalue()
        assert len(pdf_bytes) > 0

    def test_generate_pdf_contains_expected_content(self, sample_state_dict: dict):
        from app.integration.pdf.service import interview_pdf_service

        result = interview_pdf_service.generate("test-id", sample_state_dict)
        content = result.getvalue().decode("latin-1")
        assert "%PDF" in content
        assert "/Type /Page" in content

    def test_generate_pdf_different_scores(self):
        from app.integration.pdf.service import interview_pdf_service

        state = {
            "interview_id": "test-id",
            "candidate_name": "Jane Smith",
            "hiring_decision": "NO_HIRE",
            "overall_score": 3.0,
            "interview_summary": {"candidate_name": "Jane Smith", "hiring_decision": "NO_HIRE"},
            "strengths": [],
            "weaknesses": ["Poor communication"],
            "risk_factors": ["Multiple red flags"],
            "topics": [{"topic": "Python", "average_score": 3.0, "confidence_score": 4.0}],
            "questions": [],
        }
        result = interview_pdf_service.generate("test-id", state)
        content = result.getvalue().decode("latin-1")
        assert "%PDF" in content
