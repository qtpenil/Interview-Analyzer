from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeTranscript:
    def test_analyze_success(self):
        from app.tasks.analysis_tasks import analyze_transcript

        with patch("app.tasks.analysis_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.analysis_tasks.update_interview_status"):
                with patch("app.tasks.analysis_tasks.interview_graph_runner.run") as mock_run:
                    mock_run.return_value = {
                        "hiring_decision": "HIRE",
                        "overall_score": 8.5,
                        "topics": [],
                    }
                    with patch("app.tasks.analysis_tasks.save_interview_analysis_results"):
                        with patch("app.tasks.pdf_tasks.generate_pdf_report.delay"):
                            result = analyze_transcript("test-id", {"segments": []})
                            assert result["status"] == "analysis_complete"
                            assert result["hiring_decision"] == "HIRE"

    def test_analyze_cancelled(self):
        from app.tasks.analysis_tasks import analyze_transcript

        with patch("app.tasks.analysis_tasks.is_interview_cancelled", return_value=True):
            result = analyze_transcript("test-id", {"segments": []})
            assert result["status"] == "cancelled"

    def test_analyze_with_none_transcript(self):
        from app.tasks.analysis_tasks import analyze_transcript

        with patch("app.tasks.analysis_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.analysis_tasks.update_interview_status"):
                with patch("app.tasks.analysis_tasks.interview_graph_runner.run") as mock_run:
                    mock_run.return_value = {
                        "hiring_decision": "BORDERLINE",
                        "overall_score": 5.0,
                        "topics": [],
                    }
                    with patch("app.tasks.analysis_tasks.save_interview_analysis_results"):
                        with patch("app.tasks.pdf_tasks.generate_pdf_report.delay"):
                            result = analyze_transcript("test-id", None)
                            assert result["status"] == "analysis_complete"

    def test_analyze_langgraph_failure(self):
        from app.tasks.analysis_tasks import analyze_transcript

        with patch("app.tasks.analysis_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.analysis_tasks.update_interview_status"):
                with patch(
                    "app.tasks.analysis_tasks.interview_graph_runner.run", side_effect=ValueError("Graph error")
                ):
                    with pytest.raises(Exception):
                        analyze_transcript("test-id", {"segments": []})
