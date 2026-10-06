import os
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.modules.interview.InterviewModel import Interview, InterviewStatus


class TestSaveVideoFile:
    def test_save_video_file_success(self, tmp_path):
        from fastapi import UploadFile

        from app.modules.interview.service import save_video_file

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test_video.mp4"
        mock_file.file = BytesIO(b"fake video content")

        with patch("app.modules.interview.service.os.makedirs") as mock_makedirs:
            path = save_video_file(mock_file)
            assert "storage/uploads/" in path
            assert path.endswith(".mp4")
            mock_makedirs.assert_called_once()

    def test_save_video_file_no_filename(self):
        from fastapi import UploadFile

        from app.modules.interview.service import save_video_file

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        mock_file.file = BytesIO(b"fake video content")

        with patch("app.modules.interview.service.os.makedirs"):
            path = save_video_file(mock_file)
            assert path.endswith(".mp4")


class TestCreateInterview:
    def test_create_interview_success(self):
        from app.modules.interview.service import create_interview

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.id = uuid.uuid4()
            mock_interview.status = InterviewStatus.UPLOADED
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()
            mock_session.add.side_effect = lambda x: None

            with patch("app.modules.interview.service.os.path.exists", return_value=True):
                with patch("app.modules.interview.service.os.path.getsize", return_value=1024):
                    result = create_interview(
                        video_path="/tmp/test.mp4",
                        user_id=uuid.uuid4(),
                        title="Test Interview",
                    )
                    assert result is not None

    def test_create_interview_no_file_size(self):
        from app.modules.interview.service import create_interview

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.id = uuid.uuid4()
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()

            with patch("app.modules.interview.service.os.path.exists", return_value=False):
                result = create_interview(
                    video_path="/tmp/test.mp4",
                    user_id=uuid.uuid4(),
                    title="Test",
                )
                assert result is not None


class TestGetInterviewStatus:
    def test_get_interview_status_found(self):
        from app.modules.interview.service import get_interview_status

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            result = get_interview_status(uuid.uuid4(), uuid.uuid4())
            assert result is mock_interview

    def test_get_interview_status_not_found(self):
        from app.modules.interview.service import get_interview_status

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            with pytest.raises(Exception):
                get_interview_status(uuid.uuid4(), uuid.uuid4())


class TestCancelInterview:
    def test_cancel_uploaded_interview(self):
        from app.modules.interview.service import cancel_interview

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.status = InterviewStatus.UPLOADED
            mock_interview.id = uuid.uuid4()
            mock_file_result = MagicMock()
            mock_file_result.storage_path = "/tmp/video.mp4"
            mock_session.query.return_value.filter.return_value.first.side_effect = [mock_interview, mock_file_result]

            result = cancel_interview(uuid.uuid4(), uuid.uuid4())
            assert result.status == InterviewStatus.CANCELLED

    def test_cancel_completed_interview_fails(self):
        from app.modules.interview.service import cancel_interview

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.status = InterviewStatus.COMPLETED
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            with pytest.raises(Exception, match="Cannot cancel"):
                cancel_interview(uuid.uuid4(), uuid.uuid4())

    def test_cancel_interview_not_found(self):
        from app.modules.interview.service import cancel_interview

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            with pytest.raises(Exception):
                cancel_interview(uuid.uuid4(), uuid.uuid4())


class TestCheckDuplicateInterview:
    def test_duplicate_found(self):
        from app.modules.interview.service import check_duplicate_interview

        mock_db = MagicMock()
        mock_interview = MagicMock(spec=Interview)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_interview

        result = check_duplicate_interview(
            user_id=uuid.uuid4(),
            fingerprint="test_fp",
            db=mock_db,
        )
        assert result is mock_interview

    def test_no_duplicate(self):
        from app.modules.interview.service import check_duplicate_interview

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_duplicate_interview(
            user_id=uuid.uuid4(),
            fingerprint="no_match",
            db=mock_db,
        )
        assert result is None


class TestListInterviews:
    def test_list_interviews(self):
        from app.modules.interview.service import list_interviews_for_user

        mock_db = MagicMock()
        mock_db.scalar.return_value = 0
        mock_db.scalars.return_value.all.return_value = []

        result = list_interviews_for_user(
            db=mock_db,
            user_id=uuid.uuid4(),
            status=None,
            page=1,
            page_size=20,
        )
        assert result.total == 0
        assert result.items == []


class TestGetInterviewReportPath:
    def test_report_not_found(self):
        from app.modules.interview.service import get_interview_report_path

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.status = InterviewStatus.COMPLETED
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_interview,
                None,
            ]

            with pytest.raises(Exception):
                get_interview_report_path(uuid.uuid4(), uuid.uuid4())

    def test_report_found_local(self):
        from app.modules.interview.service import get_interview_report_path
        from app.modules.files.file import File

        with patch("app.modules.interview.service.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock(spec=Interview)
            mock_interview.status = InterviewStatus.COMPLETED

            mock_file = MagicMock(spec=File)
            mock_file.storage_provider = "local"
            mock_file.storage_path = "reports/test.pdf"

            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_interview,
                mock_file,
            ]

            with patch("app.modules.interview.service.read_file", return_value=b"%PDF content"):
                result = get_interview_report_path(uuid.uuid4(), uuid.uuid4())
                assert result == b"%PDF content"


class TestGetInterviewWithDetails:
    def test_owner_can_read_own_interview(self, db_session):
        from app.modules.interview.service import get_interview_with_details
        from app.modules.user.UserModel import User

        owner = User(email=f"owner-{uuid.uuid4()}@example.com", name="owner", password_hash="x")
        db_session.add(owner)
        db_session.flush()

        interview = Interview(
            user_id=owner.id,
            title="My Interview",
            status=InterviewStatus.UPLOADED,
        )
        db_session.add(interview)
        db_session.flush()

        result = get_interview_with_details(db_session, interview.id, owner.id)
        assert result is not None
        assert result.id == interview.id

    def test_other_user_cannot_read_foreign_interview(self, db_session):
        from app.modules.interview.service import get_interview_with_details
        from app.modules.user.UserModel import User

        owner = User(email=f"owner-{uuid.uuid4()}@example.com", name="owner", password_hash="x")
        attacker = User(email=f"attacker-{uuid.uuid4()}@example.com", name="attacker", password_hash="x")
        db_session.add_all([owner, attacker])
        db_session.flush()

        interview = Interview(
            user_id=owner.id,
            title="Secret Interview",
            status=InterviewStatus.UPLOADED,
        )
        db_session.add(interview)
        db_session.flush()

        result = get_interview_with_details(db_session, interview.id, attacker.id)
        assert result is None


class TestAttachQuestionsToTopics:
    def test_questions_embedded_grouped_and_ordered(self, db_session):
        from datetime import datetime
        from decimal import Decimal

        from app.core.database import Base
        from app.modules.interview.service import get_interview_with_details
        from app.modules.interviewQuestions.model import InterviewQuestion
        from app.modules.interviewTopics.interviewTopics import InterviewTopic
        from app.modules.user.UserModel import User

        owner = User(email=f"owner-{uuid.uuid4()}@example.com", name="owner", password_hash="x")
        db_session.add(owner)
        db_session.flush()

        interview = Interview(
            user_id=owner.id,
            title="Embed Interview",
            status=InterviewStatus.UPLOADED,
        )
        db_session.add(interview)
        db_session.flush()

        topic = InterviewTopic(interview_id=interview.id, topic="Python", average_score=Decimal("8.00"))
        topic2 = InterviewTopic(interview_id=interview.id, topic="System Design", average_score=Decimal("7.00"))
        db_session.add_all([topic, topic2])
        db_session.flush()

        q2 = InterviewQuestion(
            interview_id=interview.id,
            user_id=owner.id,
            topic_id=topic.id,
            category="Python",
            question_number=2,
            question="Q2?",
            answer="A2",
            average_score=Decimal("7.00"),
        )
        q1 = InterviewQuestion(
            interview_id=interview.id,
            user_id=owner.id,
            topic_id=topic.id,
            category="Python",
            question_number=1,
            question="Q1?",
            answer="A1",
            average_score=Decimal("9.00"),
        )
        db_session.add_all([q2, q1])
        db_session.flush()

        result = get_interview_with_details(db_session, interview.id, owner.id)
        assert result is not None
        topics = {t.topic: t for t in result.topics}

        python_questions = topics["Python"].questions
        assert [q["question_number"] for q in python_questions] == [1, 2]
        assert python_questions[0]["question"] == "Q1?"
        assert python_questions[0]["average_score"] == float(Decimal("9.00"))

        assert topics["System Design"].questions == []
