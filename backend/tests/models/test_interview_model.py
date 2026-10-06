from app.modules.interview.InterviewModel import HiringDecision, Interview, InterviewStatus


class TestInterviewStatus:
    def test_all_statuses_present(self):
        expected = {"UPLOADED", "PROCESSING", "TRANSCRIBING", "ANALYZING", "COMPLETED", "FAILED", "CANCELLED"}
        actual = {s.value for s in InterviewStatus}
        assert actual == expected

    def test_status_is_string_enum(self):
        assert InterviewStatus.UPLOADED.value == "UPLOADED"
        assert InterviewStatus.CANCELLED.value == "CANCELLED"


class TestHiringDecision:
    def test_all_decisions_present(self):
        expected = {"STRONG_HIRE", "HIRE", "BORDERLINE", "NO_HIRE"}
        actual = {d.value for d in HiringDecision}
        assert actual == expected


class TestInterviewModel:
    def test_model_has_required_fields(self):
        required = {
            "id",
            "user_id",
            "title",
            "status",
            "created_at",
            "updated_at",
            "overall_score",
            "technical_score",
            "communication_score",
            "confidence_score",
            "knowledge_depth",
            "experience_alignment_score",
            "hiring_decision",
            "transcript",
            "audio_fingerprint",
            "processing_started_at",
            "processing_completed_at",
            "ai_model_name",
            "ai_model_version",
        }
        columns = {c.name for c in Interview.__table__.columns}
        for field in required:
            assert field in columns, f"Missing field: {field}"

    def test_model_table_name(self):
        assert Interview.__tablename__ == "interviews"

    def test_model_relationships(self):
        from sqlalchemy.orm import RelationshipProperty

        relationships = Interview.__mapper__.relationships
        assert "user" in relationships
        assert "topics" in relationships
        assert "files" in relationships
