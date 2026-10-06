import pytest

from app.integration.langGraph.outputValidator import (
    ValidationResult,
    validate_conversation_blocks,
    validate_interview_summary,
    validate_metadata_qa,
    validate_question_evaluations,
    validate_topic_summaries,
)
from app.integration.langGraph.Schema.assessmentSchema import (
    InterviewSummary,
    QuestionEvaluation,
    TopicSummary,
)
from app.integration.langGraph.Schema.commonSchema import (
    DifficultyLevel,
    HiringDecision,
    SpeakerRole,
)
from app.integration.langGraph.Schema.interviewSchema import (
    ConversationBlock,
    MetadataAndQA,
    QuestionAnswer,
)


class TestValidateConversationBlocks:
    def test_valid_blocks_pass(self):
        blocks = [
            ConversationBlock(
                speaker_role=SpeakerRole.INTERVIEWER,
                speaker_label="Interviewer",
                text="Hello",
                start_time=0.0,
                end_time=5.0,
            ),
            ConversationBlock(
                speaker_role=SpeakerRole.CANDIDATE,
                speaker_label="Candidate",
                text="Hi",
                start_time=5.0,
                end_time=10.0,
            ),
        ]
        result = validate_conversation_blocks(blocks)
        assert result.is_valid

    def test_empty_blocks(self):
        result = validate_conversation_blocks([])
        assert not result.is_valid

    def test_blocks_missing_required_field(self):
        result = validate_conversation_blocks(["not-a-block"])
        assert not result.is_valid


class TestValidateMetadataQA:
    def test_valid_metadata(self):
        result = validate_metadata_qa(
            MetadataAndQA(
                candidate_name="John",
                claimed_experience_years=5.0,
                question_answers=[QuestionAnswer(question_id="q1", question="Q1", answer="A1")],
            )
        )
        assert result.is_valid

    def test_missing_question_answers(self):
        result = validate_metadata_qa(MetadataAndQA(question_answers=[]))
        assert not result.is_valid

    def test_empty_question_answers(self):
        result = validate_metadata_qa(MetadataAndQA(question_answers=[]))
        assert not result.is_valid


class TestValidateQuestionEvaluations:
    def test_valid_evaluations(self):
        evals = [
            QuestionEvaluation(
                question_id="q1",
                question="Q1",
                answer="A1",
                expected_answer="Expected",
                category="python",
                sub_category="basics",
                difficulty=DifficultyLevel.EASY,
                expected_experience=1.0,
                accuracy_score=8.0,
                depth_score=7.0,
                completeness_score=8.0,
                clarity_score=7.0,
                confidence_score=8.0,
                experience_alignment_score=7.0,
                feedback="Good",
            )
        ]
        result = validate_question_evaluations(evals, expected_count=1)
        assert result.is_valid

    def test_mismatched_count(self):
        evals = [
            QuestionEvaluation(
                question_id="q1",
                question="Q1",
                answer="A1",
                expected_answer="Expected",
                category="python",
                sub_category="basics",
                difficulty=DifficultyLevel.EASY,
                expected_experience=1.0,
                accuracy_score=8.0,
                depth_score=7.0,
                completeness_score=8.0,
                clarity_score=7.0,
                confidence_score=8.0,
                experience_alignment_score=7.0,
                feedback="Good",
            )
        ]
        result = validate_question_evaluations(evals, expected_count=5)
        assert not result.is_valid

    def test_empty_evaluations(self):
        result = validate_question_evaluations([], expected_count=1)
        assert not result.is_valid


class TestValidateTopicSummaries:
    def test_valid_topics(self):
        topics = [
            TopicSummary(
                topic="Python",
                total_questions=1,
                average_score=8.5,
                confidence_score=9.0,
                feedback="Good",
            )
        ]
        evaluations = [
            QuestionEvaluation(
                question_id="q1",
                question="Q1",
                answer="A1",
                expected_answer="Expected",
                category="Python",
                sub_category="basics",
                difficulty=DifficultyLevel.EASY,
                expected_experience=1.0,
                accuracy_score=8.0,
                depth_score=7.0,
                completeness_score=8.0,
                clarity_score=7.0,
                confidence_score=8.0,
                experience_alignment_score=7.0,
                feedback="Good",
            )
        ]
        result = validate_topic_summaries(topics, evaluations)
        assert result.is_valid

    def test_empty_topics(self):
        result = validate_topic_summaries([], [])
        assert not result.is_valid


class TestValidateInterviewSummary:
    def test_valid_summary(self):
        result = validate_interview_summary(
            InterviewSummary(
                overall_score=8.5,
                technical_score=8.0,
                communication_score=7.5,
                confidence_score=9.0,
                knowledge_depth=8.0,
                experience_alignment_score=7.0,
                strengths=["Technical depth"],
                weaknesses=["Communication"],
                final_feedback="Good candidate",
                hiring_decision=HiringDecision.HIRE,
            )
        )
        assert result.is_valid

    def test_missing_hiring_decision(self):
        with pytest.raises(Exception):
            InterviewSummary(
                overall_score=8.5,
            )
