from app.modules.interviewTopics.interviewTopics import InterviewTopic


class TestInterviewTopicModel:
    def test_model_has_required_fields(self):
        required = {
            "id",
            "interview_id",
            "topic",
            "average_score",
            "confidence_score",
            "strongest_concepts",
            "weakest_concepts",
            "created_at",
        }
        columns = {c.name for c in InterviewTopic.__table__.columns}
        for field in required:
            assert field in columns, f"Missing field: {field}"

    def test_model_table_name(self):
        assert InterviewTopic.__tablename__ == "interview_topics"

    def test_unique_constraint(self):
        constraints = InterviewTopic.__table__.constraints
        constraint_names = {c.name for c in constraints}
        assert "uq_interview_topic" in constraint_names

    def test_model_relationships(self):
        relationships = InterviewTopic.__mapper__.relationships
        assert "interview" in relationships
