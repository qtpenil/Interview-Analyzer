import asyncio
import json
import uuid
from datetime import datetime

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.shared.logger.logger import get_logger

from .interviewNodes import (
    batched_qa_assessment,
    interview_summary,
    metadata_qa_extractor,
    topic_aggregation,
    transcript_structuring,
)
from .interviewState import InterviewGraphState
from .Schema.commonSchema import ProcessingStatus

logger = get_logger(__name__)


class LangGraphPipelineError(Exception):
    """Raised when one or more pipeline nodes fail.

    A failed run produces no usable analysis data, so surfacing it (instead of
    letting the caller render an empty PDF) is essential for correct status.
    """

    def __init__(self, errors: list[str] | None = None):
        self.errors = errors or []
        super().__init__("; ".join(self.errors) or "LangGraph pipeline failed")


def create_graph_nodes():
    agent_builder = StateGraph(InterviewGraphState)

    # Add Nodes
    agent_builder.add_node("transcript_structuring", transcript_structuring)
    agent_builder.add_node("metadata_qa_extractor", metadata_qa_extractor)
    agent_builder.add_node("batched_qa_assessment", batched_qa_assessment)
    agent_builder.add_node("topic_aggregation", topic_aggregation)
    agent_builder.add_node("interview_summary", interview_summary)

    # Add edges
    agent_builder.add_edge(START, "transcript_structuring")
    agent_builder.add_edge("transcript_structuring", "metadata_qa_extractor")
    agent_builder.add_edge("metadata_qa_extractor", "batched_qa_assessment")
    agent_builder.add_edge("batched_qa_assessment", "topic_aggregation")
    agent_builder.add_edge("topic_aggregation", "interview_summary")
    agent_builder.add_edge("interview_summary", END)

    agent = agent_builder.compile()
    return agent


class InterviewGraphRunner:
    """
    Wrapper around the compiled LangGraph StateGraph.
    Coordinated with distributed locking, database idempotency status checks,
    and checkpoint-restore functionality.
    """

    def __init__(self):
        self._graph = create_graph_nodes()

    def run(self, transcript: list[dict] | dict | None, interview_id: str | None = None) -> dict:
        """
        Synchronous entry point. Runs the full pipeline inside a single asyncio event loop.
        """
        return asyncio.run(self._run_async(transcript, interview_id))

    async def _run_async(self, transcript: list[dict] | dict | None, interview_id: str | None) -> dict:
        if not interview_id:
            interview_id = str(uuid.uuid4())

        # 1. Idempotency Check (Phase 5)
        # Verify if task has already completed or is currently running
        from uuid import UUID

        from app.core.database import SessionLocal
        from app.modules.interview.InterviewModel import Interview, InterviewStatus

        session = SessionLocal()
        try:
            db_interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()
            if db_interview:
                if db_interview.status == InterviewStatus.COMPLETED:
                    logger.info(f"[{interview_id}] Interview is already COMPLETED. Returning cached results.")
                    return await self._format_output_from_db_or_checkpoint(db_interview, interview_id)
        finally:
            session.close()

        # 2. Concurrency Gating (Phase 2 - Pipeline Concurrency Level)
        from app.integration.langGraph.concurrency import get_concurrency_manager

        concurrency_mgr = get_concurrency_manager()

        segments = self._extract_segments(transcript)

        # ── Input diagnostics (transcript size) ─────────────────────────────
        raw_text = " ".join(str(s.get("text", "")) for s in segments if isinstance(s, dict))
        raw_chars = len(raw_text)
        raw_words = len(raw_text.split())
        logger.info(
            f"[{interview_id}] Transcript input: segments={len(segments)}, "
            f"chars={raw_chars}, words={raw_words}"
        )

        # Preprocessing, normalization, and safety rules (Phases 7 & 8)
        # Run input preprocessing: Unicode normalization, PII redaction, size limits.
        from app.integration.langGraph.security_hardening import preprocess_transcript

        processed_segments = preprocess_transcript(segments, interview_id)

        proc_text = " ".join(str(s.get("text", "")) for s in processed_segments if isinstance(s, dict))
        logger.info(
            f"[{interview_id}] Transcript after preprocessing: segments={len(processed_segments)}, "
            f"chars={len(proc_text)}, words={len(proc_text.split())}"
        )

        # 3. Concurrency Gate
        async with concurrency_mgr.gate_interview(interview_id):
            import hashlib

            from app.integration.langGraph.interviewPrompt import (
                INTERVIEW_SUMMARY_PROMPT,
                METADATA_QA_EXTRACTION_PROMPT,
                QA_ASSESSMENT_PROMPT,
                TRANSCRIPT_COMBINED_PROMPT,
            )
            from app.integration.langGraph.Schema.commonSchema import PipelineMetadata

            combined_prompts = (
                TRANSCRIPT_COMBINED_PROMPT
                + METADATA_QA_EXTRACTION_PROMPT
                + QA_ASSESSMENT_PROMPT
                + INTERVIEW_SUMMARY_PROMPT
            )
            prompt_hash = hashlib.sha256(combined_prompts.encode("utf-8")).hexdigest()[:12]

            primary_provider = settings.PRIMARY_PROVIDER
            if primary_provider == "google":
                model_name = settings.GOOGLE_AI_MODEL
                top_p = 0.0
                top_k = 1
            elif primary_provider == "openai":
                model_name = settings.OPENAI_MODEL
                top_p = None
                top_k = None
            elif primary_provider == "anthropic":
                model_name = settings.ANTHROPIC_MODEL
                top_p = None
                top_k = None
            else:
                model_name = settings.OLLAMA_MODEL
                top_p = None
                top_k = None

            metadata = PipelineMetadata(
                pipeline_version="1.0.0",
                schema_version="1.0.0",
                prompt_version=prompt_hash,
                model_name=model_name,
                provider=primary_provider,
                temperature=0.0,
                top_p=top_p,
                top_k=top_k,
                execution_timestamp=datetime.utcnow().isoformat(),
            )

            # Seed user-provided metadata (if any) from the interview record.
            # The frontend may pass claimed_experience_years at upload time; when
            # present, it takes precedence over LLM transcript extraction.
            db_claimed_experience: float | None = None
            seed_session = SessionLocal()
            try:
                db_claimed = (
                    seed_session.query(Interview)
                    .filter(Interview.id == UUID(interview_id))
                    .first()
                )
                if db_claimed and db_claimed.claimed_experience_years is not None:
                    db_claimed_experience = float(db_claimed.claimed_experience_years)
            finally:
                seed_session.close()

            initial_state = {
                "interview_id": interview_id,
                "raw_transcript": json.dumps({"segments": processed_segments}),
                "started_at": datetime.utcnow(),
                "pipeline_metadata": metadata,
                "claimed_experience_years": db_claimed_experience,
            }

            # Phase 6: Resume support via Checkpointing
            if settings.ENABLE_CHECKPOINTING:
                checkpoint = await concurrency_mgr.backend.get_checkpoint(f"checkpoint:{interview_id}")
                if checkpoint:
                    logger.info(f"[{interview_id}] Found valid checkpoint in backend. Loading and resuming.")
                    # Clear errors and reset FAILED nodes to PENDING to enable re-runs
                    if "errors" in checkpoint:
                        checkpoint["errors"] = []
                    for status_k in [
                        "transcript_processing_status",
                        "metadata_extraction_status",
                        "assessment_status",
                        "topic_aggregation_status",
                        "final_summary_status",
                    ]:
                        if checkpoint.get(status_k) == ProcessingStatus.FAILED:
                            checkpoint[status_k] = ProcessingStatus.PENDING
                    initial_state.update(checkpoint)

            # 4. Invoke the LangGraph pipeline
            logger.info(f"[{interview_id}] Invoking LangGraph StateGraph pipeline.")
            result = await self._graph.ainvoke(initial_state)

            # 5. Surface hard node failures instead of rendering an empty report.
            #    Nodes return ``errors`` + a ``*_status: FAILED`` field rather than
            #    raising, so a failed run would otherwise flow through silently and
            #    produce a skeleton-only PDF marked COMPLETED.
            failure_errors = self._collect_pipeline_errors(result)
            if failure_errors:
                logger.error(
                    f"[{interview_id}] LangGraph pipeline finished with node failures: {failure_errors}"
                )
                raise LangGraphPipelineError(failure_errors)

            return self._format_output(result)

    def _collect_pipeline_errors(self, result: dict) -> list[str]:
        """Inspect a finished graph state for node failures / accumulated errors.

        Nodes do not raise on failure (they return ``{"errors": [...], "<node>_status":
        FAILED}``), so we must detect failure by examining the resulting state. Any
        failed required node means the analysis data is unusable.
        """
        errors: list[str] = []

        # Accumulated error strings from any node.
        raw_errors = result.get("errors")
        if isinstance(raw_errors, list):
            errors.extend(str(e) for e in raw_errors if e)

        # Per-node status flags that indicate a hard failure.
        failed_status_keys = [
            "transcript_processing_status",
            "metadata_extraction_status",
            "assessment_status",
            "topic_aggregation_status",
            "final_summary_status",
        ]

        for key in failed_status_keys:
            status = result.get(key)
            if status is not None and str(getattr(status, "value", status)).upper() == "FAILED":
                errors.append(f"node '{key}' failed (status={status})")

        # De-duplicate while preserving order.
        seen: set[str] = set()
        unique: list[str] = []
        for e in errors:
            if e not in seen:
                seen.add(e)
                unique.append(e)
        return unique

    def _extract_segments(self, transcript: list[dict] | dict | None) -> list[dict]:
        if not transcript:
            return []
        elif isinstance(transcript, dict):
            return transcript.get("segments", [])
        return transcript

    async def _format_output_from_db_or_checkpoint(self, db_interview, interview_id: str) -> dict:
        # Load from checkpoint first if possible to get detailed questions/evals
        if settings.ENABLE_CHECKPOINTING:
            from app.integration.langGraph.concurrency import get_concurrency_manager

            concurrency_mgr = get_concurrency_manager()
            checkpoint = await concurrency_mgr.backend.get_checkpoint(f"checkpoint:{interview_id}")
            if checkpoint:
                return self._format_output(checkpoint)

        # Fallback to reconstructing result from database fields
        topics = []
        for t in db_interview.topics:
            topics.append(
                {
                    "topic": t.topic,
                    "average_score": float(t.average_score) if t.average_score else 0.0,
                    "confidence_score": float(t.confidence_score) if t.confidence_score else 0.0,
                    "strongest_concepts": t.strongest_concepts or [],
                    "weakest_concepts": t.weakest_concepts or [],
                    "feedback": getattr(t, "feedback", ""),
                }
            )

        return {
            "candidate_name": db_interview.title or "Candidate",
            # Default to 1 year when not provided/recorded, matching the live
            # pipeline default in metadata_qa_extractor.
            "claimed_experience_years": float(db_interview.claimed_experience_years)
            if db_interview.claimed_experience_years
            else 1.0,
            "hiring_decision": db_interview.hiring_decision.value if db_interview.hiring_decision else "borderline",
            "overall_score": float(db_interview.overall_score) if db_interview.overall_score else 0.0,
            "technical_score": float(db_interview.technical_score) if db_interview.technical_score else 0.0,
            "communication_score": float(db_interview.communication_score) if db_interview.communication_score else 0.0,
            "confidence_score": float(db_interview.confidence_score) if db_interview.confidence_score else 0.0,
            "knowledge_depth": float(db_interview.knowledge_depth) if db_interview.knowledge_depth else 0.0,
            "experience_alignment_score": float(db_interview.experience_alignment_score)
            if db_interview.experience_alignment_score
            else 0.0,
            "summary": "",
            "final_feedback": "",
            "strengths": [],
            "weaknesses": [],
            "risk_factors": [],
            "interview_summary": {},
            "question_evaluations": [],
            "topics": topics,
            "questions": [],
        }

    # ── Celery serialisation safety ──────────────────────────────────────────

    @staticmethod
    def _to_plain(obj):
        """Recursively convert Pydantic models / enums / datetimes to plain
        JSON-serialisable types.  Used as a last-resort scrub before the
        state_dict is handed to Celery's kombu serialiser."""
        from datetime import date, datetime
        from enum import Enum

        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if hasattr(obj, "model_dump"):  # any Pydantic model
            return InterviewGraphRunner._to_plain(obj.model_dump(mode="json"))
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: InterviewGraphRunner._to_plain(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [InterviewGraphRunner._to_plain(i) for i in obj]
        # last resort: stringify
        return str(obj)

    # ── Output formatter ──────────────────────────────────────────────────────

    def _format_output(self, state: dict) -> dict:
        interview_sum = state.get("interview_summary")
        topic_summaries = state.get("topic_summaries") or []
        question_evals = state.get("question_evaluations") or []

        # Extract fields from the InterviewSummary pydantic model.
        # mode="json" converts nested enums / datetimes automatically.
        if interview_sum and hasattr(interview_sum, "model_dump"):
            summary_data = interview_sum.model_dump(mode="json")
        elif isinstance(interview_sum, dict):
            summary_data = interview_sum
        else:
            summary_data = {}

        # Build topics list — always plain dicts
        topics = [(t.model_dump(mode="json") if hasattr(t, "model_dump") else t) for t in topic_summaries]

        # Build questions list — always plain dicts
        questions = [(q.model_dump(mode="json") if hasattr(q, "model_dump") else q) for q in question_evals]

        # Phase 9: pipeline metadata — must be a plain dict for Celery/kombu.
        pipeline_metadata = state.get("pipeline_metadata", {})
        if hasattr(pipeline_metadata, "model_dump"):
            pipeline_metadata = pipeline_metadata.model_dump(mode="json")
        elif not isinstance(pipeline_metadata, dict):
            pipeline_metadata = {}

        # Build hiring_decision as string (enum.value) if needed
        hiring_decision = summary_data.get("hiring_decision", "borderline")
        if hasattr(hiring_decision, "value"):
            hiring_decision = hiring_decision.value

        output = {
            "candidate_name": summary_data.get("candidate_name"),
            "claimed_experience_years": state.get("claimed_experience_years"),
            "hiring_decision": hiring_decision,
            "overall_score": summary_data.get("overall_score", 0),
            "technical_score": summary_data.get("technical_score", 0),
            "communication_score": summary_data.get("communication_score", 0),
            "confidence_score": summary_data.get("confidence_score", 0),
            "knowledge_depth": summary_data.get("knowledge_depth", 0),
            "experience_alignment_score": summary_data.get("experience_alignment_score", 0),
            "summary": summary_data.get("final_feedback", ""),
            "final_feedback": summary_data.get("final_feedback", ""),
            "strengths": summary_data.get("strengths", []),
            "weaknesses": summary_data.get("weaknesses", []),
            "risk_factors": summary_data.get("risk_factors", []),
            "interview_summary": summary_data,
            "question_evaluations": questions,
            "topics": topics,
            "questions": questions,
            "pipeline_metadata": pipeline_metadata,
        }

        # Final deep-scrub: catch any residual non-serialisable objects
        output = self._to_plain(output)

        logger.info(
            f"LangGraph output formatted [{state.get('interview_id', '?')}]: "
            f"topics={len(topics)}, questions={len(questions)}, "
            f"final_feedback_chars={len(summary_data.get('final_feedback') or '')}, "
            f"strengths={len(summary_data.get('strengths') or [])}, "
            f"weaknesses={len(summary_data.get('weaknesses') or [])}, "
            f"risk_factors={len(summary_data.get('risk_factors') or [])}, "
            f"skills_assessed={len(summary_data.get('skills_assessed') or [])}"
        )
        return output


interview_graph_runner = InterviewGraphRunner()
