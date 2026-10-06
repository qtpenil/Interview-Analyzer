from app.modules.interviewQuestions.model import InterviewQuestion


class TestInterviewQuestionModel:
    def test_model_has_required_fields(self):
        required = {
            "id",
            "interview_id",
            "user_id",
            "topic_id",
            "category",
            "sub_category",
            "question_number",
            "question",
            "answer",
            "difficulty",
            "average_score",
            "strong_concepts",
            "weak_concepts",
            "feedback",
            "created_at",
            "updated_at",
        }
        columns = {c.name for c in InterviewQuestion.__table__.columns}
        for field in required:
            assert field in columns, f"Missing field: {field}"

    def test_model_table_name(self):
        assert InterviewQuestion.__tablename__ == "interview_questions"

    def test_unique_constraint(self):
        constraints = InterviewQuestion.__table__.constraints
        constraint_names = {c.name for c in constraints}
        assert "uq_interview_question_number" in constraint_names

    def test_feedback_column_nullable_text(self):
        feedback = InterviewQuestion.__table__.columns["feedback"]
        assert feedback.nullable
        assert str(feedback.type).lower().startswith("text")

    def test_difficulty_uses_shared_enum(self):
        from app.integration.langGraph.Schema.commonSchema import DifficultyLevel

        difficulty = InterviewQuestion.__table__.columns["difficulty"]
        assert difficulty.type.enums == [item.name for item in DifficultyLevel]

    def test_average_score_is_decimal(self):
        average_score = InterviewQuestion.__table__.columns["average_score"]
        assert not average_score.nullable
