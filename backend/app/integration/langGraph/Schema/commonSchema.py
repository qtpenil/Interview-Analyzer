from enum import Enum

from pydantic import BaseModel


class SpeakerRole(str, Enum):
    """
    Speaker role in interview.

    INTERVIEWER: Person asking questions, controlling flow
    CANDIDATE:   Person answering questions, describing experience
    UNKNOWN:     Could not determine role (edge case)
    """

    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"
    UNKNOWN = "unknown"

    @property
    def is_interviewer(self) -> bool:
        """Check if this is the interviewer."""
        return self == SpeakerRole.INTERVIEWER

    @property
    def is_candidate(self) -> bool:
        """Check if this is the candidate."""
        return self == SpeakerRole.CANDIDATE


class DifficultyLevel(str, Enum):
    """
    Interview question difficulty level.

    Used to calibrate expected answers and score interpretation:
    - EASY:   Junior level, fundamentals only
    - MEDIUM: Mid-level, some depth expected
    - HARD:   Senior level, deep understanding required
    - EXPERT: Staff/Principal level, architectural thinking required

    Scoring interpretation shifts with difficulty:
    - EASY question: accuracy_score 5/10 = candidate misses basics
    - HARD question: accuracy_score 5/10 = candidate has working knowledge
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

    @property
    def typical_years(self) -> float:
        """Typical years of experience to handle this difficulty."""
        mapping = {
            DifficultyLevel.EASY: 0.5,
            DifficultyLevel.MEDIUM: 2.0,
            DifficultyLevel.HARD: 5.0,
            DifficultyLevel.EXPERT: 8.0,
        }
        return mapping.get(self, 0.0)

    @property
    def pass_threshold(self) -> float:
        """Minimum accuracy_score to consider this question "passed"."""
        # EASY: higher bar (candidate should know basics)
        # EXPERT: lower bar (any grasp is good)
        mapping = {
            DifficultyLevel.EASY: 7.0,
            DifficultyLevel.MEDIUM: 6.0,
            DifficultyLevel.HARD: 5.0,
            DifficultyLevel.EXPERT: 4.0,
        }
        return mapping.get(self, 5.0)


class HiringDecision(str, Enum):
    """
    Final hiring decision based on interview performance.

    Decision framework (based on overall_score, topic scores, experience_alignment):

    STRONG_HIRE (overall ≥ 8.5)
      Exceptional performance. Consistently strong across topics.
      No topic weak (all ≥ 7). Experience fully validated.
      → Recommend immediate hire.

    HIRE (overall ≥ 7, no topic < 4)
      Solid candidate with minor gaps that can be onboarded.
      → Recommend hire.

    BORDERLINE (5 ≤ overall < 7, OR any topic critically weak < 4)
      Mixed performance. Real strengths offset by real gaps.
      → Recommend human panel review before decision.

    REJECT (overall < 6, OR 1+ topic critically weak < 4)
      Multiple important weaknesses.
      → Recommend rejection.

    STRONG_REJECT (overall < 4, OR core topics Java/OOP/System Design < 3)
      Fundamental gaps. Major experience mismatch.
      → Recommend rejection.

    Calibration rule:
      experience_alignment_score < 5 is a strong signal toward REJECT/STRONG_REJECT
      regardless of raw scores. Claimed experience but lacks fundamentals = red flag.
    """

    STRONG_REJECT = "strong_reject"
    REJECT = "reject"
    BORDERLINE = "borderline"
    HIRE = "hire"
    STRONG_HIRE = "strong_hire"

    @property
    def is_positive(self) -> bool:
        """Is this a positive hiring decision?"""
        return self in (HiringDecision.HIRE, HiringDecision.STRONG_HIRE)

    @property
    def is_negative(self) -> bool:
        """Is this a negative hiring decision?"""
        return self in (HiringDecision.REJECT, HiringDecision.STRONG_REJECT)

    @property
    def is_undecided(self) -> bool:
        """Does this decision require human review?"""
        return self == HiringDecision.BORDERLINE

    @staticmethod
    def from_scores(
        overall_score: float,
        topic_scores: dict[str, float],
        experience_alignment: float,
        core_topics: list[str] | None = None,
    ) -> "HiringDecision":
        """
        Helper to compute hiring decision from scores.

        Args:
            overall_score: Mean of all aggregate scores (0–10)
            topic_scores: Dict of topic → average_score
            experience_alignment: experience_alignment_score (0–10)
            core_topics: List of critical topic names (e.g., ['Java', 'OOP', 'System Design'])

        Returns:
            HiringDecision based on decision framework above.
        """
        if core_topics is None:
            core_topics = ["Java", "OOP", "System Design"]

        # Check core topics first (strongest signal)
        core_avg = sum(
            score for topic, score in topic_scores.items() if any(core in topic for core in core_topics)
        ) / len([s for t, s in topic_scores.items() if any(c in t for c in core_topics)])

        # Check critical weakness: claimed experience but lacks fundamentals
        if experience_alignment < 5.0:
            if overall_score < 6.0:
                return HiringDecision.STRONG_REJECT
            return HiringDecision.REJECT

        # Standard framework
        if overall_score >= 8.5 and all(s >= 7.0 for s in topic_scores.values()):
            return HiringDecision.STRONG_HIRE
        elif overall_score >= 7.0 and all(s >= 4.0 for s in topic_scores.values()):
            return HiringDecision.HIRE
        elif overall_score < 4.0 or (core_avg < 3.0):
            return HiringDecision.STRONG_REJECT
        elif overall_score < 6.0 or any(s < 4.0 for s in topic_scores.values()):
            return HiringDecision.REJECT
        else:
            return HiringDecision.BORDERLINE


class ProcessingStatus(str, Enum):
    """
    Status of a processing node.

    PENDING:     Waiting to run
    IN_PROGRESS: Currently executing
    COMPLETED:   Finished successfully
    FAILED:      Encountered error
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        """Has processing finished (successfully or not)?"""
        return self in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED)

    @property
    def is_success(self) -> bool:
        """Did processing succeed?"""
        return self == ProcessingStatus.COMPLETED


class PipelineMetadata(BaseModel):
    pipeline_version: str
    schema_version: str
    prompt_version: str
    model_name: str
    provider: str
    temperature: float
    top_p: float | None = None
    top_k: int | None = None
    execution_timestamp: str
