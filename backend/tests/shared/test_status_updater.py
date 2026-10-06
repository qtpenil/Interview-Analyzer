import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.modules.interview.InterviewModel import InterviewStatus


class TestUpdateInterviewStatus:
    def test_update_success(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import update_interview_status

            update_interview_status(str(uuid.uuid4()), InterviewStatus.PROCESSING)
            assert mock_interview.status == InterviewStatus.PROCESSING
            mock_session.commit.assert_called_once()

    def test_update_interview_not_found(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            from app.shared.db.status_updater import update_interview_status

            update_interview_status(str(uuid.uuid4()), InterviewStatus.PROCESSING)
            mock_session.commit.assert_not_called()

    def test_update_with_processing_time(self):
        from datetime import datetime

        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            now = datetime.utcnow()
            from app.shared.db.status_updater import update_interview_status

            update_interview_status(str(uuid.uuid4()), InterviewStatus.COMPLETED, processing_completed_at=now)
            assert mock_interview.processing_completed_at == now


class TestIsInterviewCancelled:
    def test_cancelled_returns_true(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_interview.status = InterviewStatus.CANCELLED
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import is_interview_cancelled

            assert is_interview_cancelled(str(uuid.uuid4())) is True

    def test_not_cancelled_returns_false(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_interview.status = InterviewStatus.PROCESSING
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import is_interview_cancelled

            assert is_interview_cancelled(str(uuid.uuid4())) is False

    def test_interview_not_found(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            from app.shared.db.status_updater import is_interview_cancelled

            assert is_interview_cancelled(str(uuid.uuid4())) is False

    def test_db_error_returns_false(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.side_effect = Exception("DB error")

            from app.shared.db.status_updater import is_interview_cancelled

            assert is_interview_cancelled(str(uuid.uuid4())) is False


class TestSaveInterviewAnalysisResults:
    def test_save_results_success(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_interview.topics = []
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import save_interview_analysis_results

            state_dict = {
                "overall_score": 8.5,
                "technical_score": 8.0,
                "hiring_decision": "HIRE",
                "topics": [],
            }
            save_interview_analysis_results(str(uuid.uuid4()), state_dict)
            mock_session.commit.assert_called_once()

    def test_save_results_interview_not_found(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            from app.shared.db.status_updater import save_interview_analysis_results

            save_interview_analysis_results(str(uuid.uuid4()), {})
            mock_session.commit.assert_not_called()


class TestSaveAnalysisResultsTopicQuestionLinking:
    """Regression: topic_id must never be None on questions for a brand-new topic.

    Previously, InterviewQuestion objects captured db_topic.id BEFORE the INSERT
    flush assigned it, baking in None for every question when the topic was being
    created for the first time.
    """

    def _evaluation_dict(self, question_id, score):
        return {
            "question_id": question_id,
            "question": f"{question_id}?",
            "answer": f"A for {question_id}",
            "expected_answer": "expected",
            "category": "Python",
            "sub_category": "sub1",
            "difficulty": "medium",
            "expected_experience": 3.0,
            "accuracy_score": score,
            "depth_score": score,
            "completeness_score": score,
            "clarity_score": score,
            "confidence_score": score,
            "experience_alignment_score": score,
            "strong_concepts": ["decorators"] if question_id == "q1" else [],
            "missing_concepts": [] if question_id == "q1" else ["asyncio"],
            "strengths": [],
            "weaknesses": [],
            "feedback": "Good" if question_id == "q1" else "",
        }

    def test_new_topic_questions_get_topic_id(self):
        from app.modules.interviewQuestions.model import InterviewQuestion
        from app.modules.interviewTopics.interviewTopics import InterviewTopic
        from app.shared.db.status_updater import save_interview_analysis_results

        new_topic_id = uuid.uuid4()
        interview = MagicMock()
        interview.id = uuid.uuid4()
        interview.user_id = uuid.uuid4()

        session = MagicMock()
        # query order: interview lookup -> topic lookup (None = new) -> topic_stats (None = new)
        session.query.return_value.filter.return_value.first.side_effect = [interview, None]
        session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        def fake_flush(*args, **kwargs):
            # A real flush() assigns pending PKs. Assign them ONLY at flush time —
            # this is what makes the test a genuine regression: with no flush
            # before the question loop, every question captured topic_id=None.
            for call in session.add.call_args_list:
                obj = call.args[0]
                if isinstance(obj, InterviewTopic) and getattr(obj, "id", None) is None:
                    obj.id = new_topic_id

        session.flush.side_effect = fake_flush

        with (
            patch("app.shared.db.status_updater.SessionLocal", return_value=session),
            patch("app.shared.db.status_updater._invalidate_dashboard_cache") as mock_invalidate,
        ):
            save_interview_analysis_results(
                str(interview.id),
                {
                    "overall_score": 8.5,
                    "hiring_decision": "HIRE",
                    "topics": [
                        {
                            "topic": "Python",
                            "average_score": 8.5,
                            "confidence_score": 9.0,
                            "strongest_concepts": ["decorators"],
                            "weakest_concepts": ["asyncio"],
                        }
                    ],
                    "question_evaluations": [
                        self._evaluation_dict("q1", 8.0),
                        self._evaluation_dict("q2", 9.0),
                    ],
                },
            )

        added_questions = [
            obj
            for call in session.add.call_args_list
            for obj in (call.args + tuple(call.kwargs.values()))
            if isinstance(obj, InterviewQuestion)
        ]
        assert len(added_questions) == 2
        for question in added_questions:
            assert question.topic_id is not None
            assert question.topic_id == new_topic_id
            assert question.interview_id == interview.id
            assert question.user_id == interview.user_id

        # One flush assigns db_topic.id, another assigns db_question.id; both kept.
        assert session.flush.call_count >= 2
        # The topic row itself got the new PK and the questions it owns belong to it.
        added_topic = next(
            (obj for call in session.add.call_args_list for obj in (call.args + tuple(call.kwargs.values()))
             if isinstance(obj, InterviewTopic)),
            None,
        )
        assert added_topic is not None
        assert added_topic.id == new_topic_id
        mock_invalidate.assert_called_once()
        session.commit.assert_called_once()


class TestUpdateInterviewFields:
    def test_update_field_success(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import update_interview_fields

            update_interview_fields(str(uuid.uuid4()), transcript="test transcript")
            assert mock_interview.transcript == "test transcript"
            mock_session.commit.assert_called_once()

    def test_update_nonexistent_field_skipped(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_interview = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_interview

            from app.shared.db.status_updater import update_interview_fields

            update_interview_fields(str(uuid.uuid4()), nonexistent_field="value")
            mock_session.commit.assert_called_once()

    def test_update_interview_not_found(self):
        with patch("app.shared.db.status_updater.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            from app.shared.db.status_updater import update_interview_fields

            update_interview_fields(str(uuid.uuid4()), transcript="test")
            mock_session.commit.assert_not_called()


class TestComputeAverageScore:
    def test_formula(self):
        from app.shared.db.status_updater import _compute_average_score

        assert _compute_average_score(1, 2, 3, 4, 5) == Decimal("3.00")

    def test_matches_topic_aggregation_shape(self):
        from app.shared.db.status_updater import _compute_average_score

        result = _compute_average_score(8.5, 9.0, 7.0, 8.0, 9.5)
        assert result == Decimal(str((8.5 + 9.0 + 7.0 + 8.0 + 9.5) / 5.0))


class TestExtractQuestionNumber:
    def test_ordinal_question_id(self):
        from app.shared.db.status_updater import _extract_question_number

        assert _extract_question_number("q12") == 12
        assert _extract_question_number("question3") == 3
        assert _extract_question_number("q100") == 100

    def test_plain_number_string(self):
        from app.shared.db.status_updater import _extract_question_number

        assert _extract_question_number("12") == 12

    def test_no_trailing_digits_returns_zero(self):
        from app.shared.db.status_updater import _extract_question_number

        assert _extract_question_number("q") == 0
        assert _extract_question_number("") == 0
        assert _extract_question_number(None) == 0
        assert _extract_question_number("abc") == 0


class TestIncrementalMean:
    def test_incremental_update(self):
        from app.shared.db.status_updater import _incremental_mean

        # (8.0 * 2 + 10.0) / 3 = 26.0 / 3 = 8.666...
        result = _incremental_mean(Decimal("8.00"), 2, 10.0)
        assert result == Decimal(str(26.0 / 3))

    def test_first_value(self):
        from app.shared.db.status_updater import _incremental_mean

        assert _incremental_mean(Decimal("0"), 0, 5.0) == Decimal("5.00")


class TestBuildConceptToQuestionIds:
    def test_maps_questions_listing_concept_exactly(self):
        from app.shared.db.status_updater import _build_concept_to_question_ids

        uid_a = uuid.uuid4()
        uid_b = uuid.uuid4()
        evals = [
            SimpleNamespace(question_id="q1", strong_concepts=["decorators"], missing_concepts=[]),
            SimpleNamespace(question_id="q2", strong_concepts=["decorators", "generators"], missing_concepts=[]),
            SimpleNamespace(question_id="q3", strong_concepts=["asyncio"], missing_concepts=["generators"]),
        ]
        mapping = {"q1": uid_a, "q2": uid_b, "q3": uuid.uuid4()}

        result = _build_concept_to_question_ids(
            ["decorators", "generators"],
            ["generators"],
            evals,
            mapping,
        )

        assert result["strongest"]["decorators"] == {uid_a, uid_b}
        # "asyncio" is only q3's strong concept — not part of the topic's
        # strongest_concepts list, so it must not appear as a key.
        assert "asyncio" not in result["strongest"]
        assert result["weakest"]["generators"] == {mapping["q3"]}

    def test_empty_concepts(self):
        from app.shared.db.status_updater import _build_concept_to_question_ids

        result = _build_concept_to_question_ids([], [], [], {})
        assert result == {"strongest": {}, "weakest": {}}


class TestUpdateQuestionBounds:
    def test_seeds_bounds_on_empty_stats(self):
        from app.shared.db.status_updater import _update_question_bounds

        stats = SimpleNamespace(
            highest_scored_question_id=None,
            highest_scored_question_score=None,
            lowest_scored_question_id=None,
            lowest_scored_question_score=None,
        )
        questions = [
            SimpleNamespace(id=uuid.uuid4(), average_score=Decimal("4.00")),
            SimpleNamespace(id=uuid.uuid4(), average_score=Decimal("9.00")),
        ]
        _update_question_bounds(stats, questions)

        assert stats.highest_scored_question_id == questions[1].id
        assert stats.highest_scored_question_score == Decimal("9.00")
        assert stats.lowest_scored_question_id == questions[0].id
        assert stats.lowest_scored_question_score == Decimal("4.00")

    def test_does_not_lower_existing_high(self):
        from app.shared.db.status_updater import _update_question_bounds

        old_high = uuid.uuid4()
        stats = SimpleNamespace(
            highest_scored_question_id=old_high,
            highest_scored_question_score=Decimal("8.00"),
            lowest_scored_question_id=None,
            lowest_scored_question_score=None,
        )
        questions = [SimpleNamespace(id=uuid.uuid4(), average_score=Decimal("7.00"))]
        _update_question_bounds(stats, questions)

        assert stats.highest_scored_question_id == old_high
        assert stats.highest_scored_question_score == Decimal("8.00")
        assert stats.lowest_scored_question_id == questions[0].id

    def test_skips_empty_list(self):
        from app.shared.db.status_updater import _update_question_bounds

        stats = SimpleNamespace(
            highest_scored_question_id=None,
            highest_scored_question_score=None,
            lowest_scored_question_id=None,
            lowest_scored_question_score=None,
        )
        _update_question_bounds(stats, [])
        assert stats.highest_scored_question_id is None
