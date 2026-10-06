import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


class TestGeneratePDFReport:
    def test_generate_pdf_success(self, sample_state_dict: dict):
        from app.tasks.pdf_tasks import generate_pdf_report

        with patch("app.tasks.pdf_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.pdf_tasks.interview_pdf_service.generate") as mock_generate:
                pdf_buffer = BytesIO(b"%PDF-1.4 fake pdf content")
                mock_generate.return_value = pdf_buffer

                with patch("app.tasks.pdf_tasks.save_file") as mock_save:
                    mock_save.return_value = "storage/reports/interview/id/summary.pdf"

                    with patch("app.tasks.pdf_tasks.SessionLocal") as mock_session:
                        mock_db = MagicMock()
                        mock_session.return_value = mock_db
                        mock_db.query.return_value.filter.return_value.first.return_value = None

                        with patch("app.tasks.pdf_tasks.update_interview_status"):
                            result = generate_pdf_report(str(uuid.uuid4()), sample_state_dict)
                            assert result["status"] == "completed"
                            assert result["pdf_path"] == "storage/reports/interview/id/summary.pdf"

    def test_generate_pdf_cancelled(self, sample_state_dict: dict):
        from app.tasks.pdf_tasks import generate_pdf_report

        with patch("app.tasks.pdf_tasks.is_interview_cancelled", return_value=True):
            result = generate_pdf_report(str(uuid.uuid4()), sample_state_dict)
            assert result["status"] == "cancelled"

    def test_generate_pdf_save_failure(self, sample_state_dict: dict):
        from app.tasks.pdf_tasks import generate_pdf_report

        with patch("app.tasks.pdf_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.pdf_tasks.interview_pdf_service.generate") as mock_generate:
                pdf_buffer = BytesIO(b"pdf content")
                mock_generate.return_value = pdf_buffer

                with patch("app.tasks.pdf_tasks.save_file", side_effect=Exception("Storage save failed")):
                    with pytest.raises(Exception):
                        generate_pdf_report(str(uuid.uuid4()), sample_state_dict)

    def test_generate_pdf_saves_file_record(self, sample_state_dict: dict):
        from app.tasks.pdf_tasks import generate_pdf_report

        with patch("app.tasks.pdf_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.pdf_tasks.interview_pdf_service.generate") as mock_generate:
                pdf_buffer = BytesIO(b"%PDF-1.4 content")
                mock_generate.return_value = pdf_buffer

                with patch("app.tasks.pdf_tasks.save_file", return_value="storage/reports/interview/id/summary.pdf"):
                    with patch("app.tasks.pdf_tasks.SessionLocal") as mock_session:
                        mock_db = MagicMock()
                        mock_session.return_value = mock_db
                        existing_file = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = existing_file

                        with patch("app.tasks.pdf_tasks.update_interview_status"):
                            result = generate_pdf_report(str(uuid.uuid4()), sample_state_dict)
                            assert existing_file.storage_provider == "local"
                            mock_db.commit.assert_called_once()
