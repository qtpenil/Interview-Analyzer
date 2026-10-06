import asyncio
import json
from collections import defaultdict

from app.core.config import settings
from app.shared.logger.logger import get_logger

from .interviewPrompt import (
    INTERVIEW_SUMMARY_CHAT_PROMPT,
    METADATA_QA_EXTRACTION_CHAT_PROMPT,
    QA_ASSESSMENT_CHAT_PROMPT,
    TRANSCRIPT_COMBINED_CHAT_PROMPT,
)

# Import schemas and states
from .interviewState import InterviewGraphState

# Hardening layer imports
from .logger_decorator import log_node_execution
from .retryManager import retry_manager
from .Schema.assessmentSchema import (
    InterviewSummary,
    QuestionEvaluation,
    QuestionEvaluationList,
    TopicSummary,
)
from .Schema.commonSchema import ProcessingStatus
from .Schema.interviewSchema import (
    ConversationBlockList,
    MetadataAndQA,
    ProcessedSegment,
    QuestionAnswer,
    RawSegment,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Node 0 — Transcript Structuring
# ---------------------------------------------------------------------------


@log_node_execution("transcript_structuring")
async def transcript_structuring(state: InterviewGraphState):
    """
    Converts raw Whisper transcript JSON into typed ConversationBlocks.
    """
    raw = state["raw_transcript"]
    interview_id = state.get("interview_id", "unknown")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "errors": [f"Failed to parse transcript JSON: {e}"],
            "transcript_processing_status": ProcessingStatus.FAILED,
        }

    raw_segments = [RawSegment(start=s["start"], end=s["end"], text=s["text"]) for s in data.get("segments", [])]
    processed_segments = [
        ProcessedSegment(
            start_time=seg.start,
            end_time=seg.end,
            text=seg.text,
        )
        for seg in raw_segments
    ]

    chunk_lines = [f"[{i}] {s.start_time:.1f}→{s.end_time:.1f} | {s.text}" for i, s in enumerate(processed_segments)]

    sample_size = min(30, len(chunk_lines))
    sample_text = "\n".join(chunk_lines[:sample_size])
    full_text = "\n".join(chunk_lines)

    payload = {
        "sample_size": sample_size,
        "sample": sample_text,
        "chunks": full_text,
    }

    # Validation retry loop
    max_validation_attempts = 2
    validation_err = None

    for attempt in range(1, max_validation_attempts + 1):
        try:
            result: ConversationBlockList = await retry_manager.invoke_structured(
                node_name="transcript_structuring",
                interview_id=interview_id,
                prompt=TRANSCRIPT_COMBINED_CHAT_PROMPT,
                schema=ConversationBlockList,
                payload=payload,
            )

            # Validate output
            from app.integration.langGraph.outputValidator import validate_conversation_blocks

            val_res = validate_conversation_blocks(result.blocks)
            if val_res.is_valid:
                logger.info(
                    f"[{interview_id}] transcript_structuring OK: blocks={len(result.blocks)}, "
                    f"sample_chars={len(sample_text)}, full_chars={len(full_text)}"
                )
                return {
                    "conversation_blocks": result.blocks,
                    "transcript_processing_status": ProcessingStatus.COMPLETED,
                }
            else:
                validation_err = val_res.error_message
                logger.warning(
                    f"[{interview_id}] transcript_structuring validation attempt {attempt} failed: {validation_err}"
                )
        except Exception as e:
            validation_err = str(e)
            logger.warning(
                f"[{interview_id}] transcript_structuring attempt {attempt} raised exception: {validation_err}"
            )

    return {
        "errors": [f"transcript_structuring validation failed: {validation_err}"],
        "transcript_processing_status": ProcessingStatus.FAILED,
    }


# ---------------------------------------------------------------------------
# Node 1 — Candidate Metadata + QA Extraction
# ---------------------------------------------------------------------------


@log_node_execution("metadata_qa_extractor")
async def metadata_qa_extractor(state: InterviewGraphState):
    """
    Single LLM call that reads the full structured transcript and simultaneously:
    1. Extracts candidate metadata (name, experience, roles, intro summary).
    2. Extracts all interview question-answer pairs including follow-ups.
    """
    blocks = state["conversation_blocks"]
    interview_id = state.get("interview_id", "unknown")

    block_lines = "\n".join(f"[{i}] {b.speaker_role.value.upper()}: {b.text}" for i, b in enumerate(blocks))

    payload = {"blocks": block_lines}

    # Validation retry loop
    max_validation_attempts = 2
    validation_err = None

    for attempt in range(1, max_validation_attempts + 1):
        try:
            result: MetadataAndQA = await retry_manager.invoke_structured(
                node_name="metadata_qa_extractor",
                interview_id=interview_id,
                prompt=METADATA_QA_EXTRACTION_CHAT_PROMPT,
                schema=MetadataAndQA,
                payload=payload,
            )

            # Validate output
            from app.integration.langGraph.outputValidator import validate_metadata_qa

            val_res = validate_metadata_qa(result)
            if val_res.is_valid:
                # Prefer the user-provided experience seeded from the interview
                # record; only fall back to LLM transcript extraction when the
                # user did not supply a value.
                existing_experience = state.get("claimed_experience_years")
                if existing_experience is None:
                    claimed_experience = (
                        result.claimed_experience_years
                        if result.claimed_experience_years is not None
                        else 1.0
                    )
                else:
                    claimed_experience = existing_experience

                logger.info(
                    f"[{interview_id}] metadata_qa_extractor OK: candidate={result.candidate_name!r}, "
                    f"experience={claimed_experience}, "
                    f"qa_pairs={len(result.question_answers)}, "
                    f"intro_chars={len(result.self_introduction_summary or '')}"
                )
                return {
                    "candidate_name": result.candidate_name,
                    "claimed_experience_years": claimed_experience,
                    "current_role": result.current_role,
                    "target_role": result.target_role,
                    "self_introduction_summary": result.self_introduction_summary,
                    "question_answers": result.question_answers,
                    "metadata_extraction_status": ProcessingStatus.COMPLETED,
                }
            else:
                validation_err = val_res.error_message
                logger.warning(
                    f"[{interview_id}] metadata_qa_extractor validation attempt {attempt} failed: {validation_err}"
                )
        except Exception as e:
            validation_err = str(e)
            logger.warning(
                f"[{interview_id}] metadata_qa_extractor attempt {attempt} raised exception: {validation_err}"
            )

    return {
        "errors": [f"metadata_qa_extractor validation failed: {validation_err}"],
        "metadata_extraction_status": ProcessingStatus.FAILED,
    }


# ---------------------------------------------------------------------------
# Node 2 — Batched QA Assessment + Topic Detection
# ---------------------------------------------------------------------------


@log_node_execution("batched_qa_assessment")
async def batched_qa_assessment(state: InterviewGraphState):
    """
    Assess all Q&A pairs in batches to avoid token/context window limits.
    """
    question_answers = state["question_answers"]
    claimed_experience_years = state.get("claimed_experience_years")
    candidate_name = state.get("candidate_name")
    interview_id = state.get("interview_id", "unknown")

    experience_context = (
        f"{claimed_experience_years} years of claimed experience"
        if claimed_experience_years is not None
        else "claimed experience not provided"
    )
    if candidate_name:
        experience_context = f"Candidate: {candidate_name}. {experience_context}"

    # Split into batches (consolidation with MAX_BATCH_SIZE is handled by using settings.QUESTION_BATCH_SIZE)
    batches = [
        question_answers[i : i + settings.QUESTION_BATCH_SIZE]
        for i in range(0, len(question_answers), settings.QUESTION_BATCH_SIZE)
    ]

    all_evaluations = []
    batch_results = {}

    from app.integration.langGraph.outputValidator import validate_question_evaluations

    async def _process_batch(
        batch_num: int, batch: list[QuestionAnswer]
    ) -> tuple[str, list[QuestionEvaluation], str | None]:
        """Assess a single batch of questions, returning (batch_id, evaluations, error)."""
        batch_id = f"batch_{batch_num}_{len(batches)}"

        qa_lines = "\n\n".join(
            f"[{qa.question_id}] QUESTION: {qa.question}\n[{qa.question_id}] ANSWER: {qa.answer}" for qa in batch
        )

        batch_context = f"Batch {batch_num}/{len(batches)} ({len(batch)} questions). {experience_context}"

        payload = {
            "experience_context": batch_context,
            "question_answers": qa_lines,
        }

        # Individual batch validation retry loop
        max_validation_attempts = 2
        batch_evals = []
        batch_err = None

        for attempt in range(1, max_validation_attempts + 1):
            try:
                result: QuestionEvaluationList = await retry_manager.invoke_structured(
                    node_name=f"batched_qa_assessment_{batch_id}",
                    interview_id=interview_id,
                    prompt=QA_ASSESSMENT_CHAT_PROMPT,
                    schema=QuestionEvaluationList,
                    payload=payload,
                )

                # Validate this specific batch result
                val_res = validate_question_evaluations(result.evaluations, len(batch))
                if val_res.is_valid:
                    batch_evals = result.evaluations
                    batch_err = None
                    break
                else:
                    batch_err = val_res.error_message
                    logger.warning(
                        f"[{interview_id}] Batch {batch_num} validation attempt {attempt} failed: {batch_err}"
                    )
            except Exception as e:
                batch_err = str(e)
                logger.warning(f"[{interview_id}] Batch {batch_num} attempt {attempt} raised exception: {batch_err}")

        return batch_id, batch_evals, batch_err

    # Process all batches concurrently — they are fully independent LLM calls,
    # and the retry manager gates them at MAX_CONCURRENT_LLM_REQUESTS.
    # gather() preserves input order, so results map back to batches cleanly.
    batch_results_raw = await asyncio.gather(
        *(_process_batch(batch_num, batch) for batch_num, batch in enumerate(batches, 1))
    )

    all_evaluations = []
    batch_results = {}

    for batch_num, (batch_id, batch_evals, batch_err) in enumerate(batch_results_raw, 1):
        if batch_err:
            return {
                "errors": [f"batched_qa_assessment failed at {batch_id}: {batch_err}"],
                "assessment_status": ProcessingStatus.FAILED,
            }

        batch_results[batch_id] = {
            "status": "success",
            "input_count": len(batches[batch_num - 1]),
            "output_count": len(batch_evals),
        }
        all_evaluations.extend(batch_evals)

    # Perform a final validation of all combined evaluations
    final_val = validate_question_evaluations(all_evaluations, len(question_answers))
    if not final_val.is_valid:
        return {
            "errors": [f"batched_qa_assessment final validation failed: {final_val.error_message}"],
            "assessment_status": ProcessingStatus.FAILED,
        }

    output = {
        "question_evaluations": all_evaluations,
        "assessment_status": ProcessingStatus.COMPLETED,
        "batch_summary": {
            "total_questions_input": len(question_answers),
            "total_questions_evaluated": len(all_evaluations),
            "total_batches": len(batches),
            "per_batch": batch_results,
        },
    }

    logger.info(
        f"[{interview_id}] batched_qa_assessment OK: input={len(question_answers)}, "
        f"evaluated={len(all_evaluations)}, batches={len(batches)}, "
        f"sample_scores="
        f"{[round(e.accuracy_score, 1) for e in all_evaluations[:5]]}"
    )

    return output


# ---------------------------------------------------------------------------
# Node 3 — Topic Aggregation (fully deterministic, no LLM)
# ---------------------------------------------------------------------------


@log_node_execution("topic_aggregation")
async def topic_aggregation(state: InterviewGraphState):
    """
    Aggregates QuestionEvaluations by topic and generates feedback deterministically.
    """
    interview_id = state.get("interview_id", "unknown")
    evaluations: list[QuestionEvaluation] = state["question_evaluations"]

    topic_buckets: dict[str, list[QuestionEvaluation]] = defaultdict(list)
    for ev in evaluations:
        topic_buckets[ev.category].append(ev)

    def top_concepts(concepts: list[str], k: int = 5) -> list[str]:
        freq: dict[str, int] = defaultdict(int)
        for c in concepts:
            freq[c.lower()] += 1
        return [c for c, _ in sorted(freq.items(), key=lambda x: -x[1])[:k]]

    def _generate_feedback(avg: float, strongest: list[str], weakest: list[str]) -> str:
        strong_str = ", ".join(strongest[:3]) if strongest else None
        weak_str = ", ".join(weakest[:3]) if weakest else None

        if avg >= 7.5:
            base = "Strong understanding demonstrated across this topic."
            detail = f" Standout concepts include {strong_str}." if strong_str else ""
            caveat = f" Minor gaps remain around {weak_str}." if weak_str else ""
            return base + detail + caveat

        if avg >= 5.0:
            base = "Shows working knowledge but some concepts need strengthening."
            detail = f" Solid grasp of {strong_str}." if strong_str else ""
            gap = f" Key gaps: {weak_str}." if weak_str else ""
            return base + detail + gap

        base = "Topic requires further study and practical exposure."
        gap = f" Priority areas to address: {weak_str}." if weak_str else ""
        anchor = f" Some familiarity evident in {strong_str}." if strong_str else ""
        return base + gap + anchor

    final_summaries: list[TopicSummary] = []

    for topic, evs in topic_buckets.items():
        n = len(evs)
        avg = round(
            sum(
                (e.accuracy_score + e.depth_score + e.completeness_score + e.clarity_score + e.confidence_score) / 5
                for e in evs
            )
            / n,
            2,
        )
        avg_confidence = round(sum(e.confidence_score for e in evs) / n, 2)
        strongest = top_concepts([c for e in evs for c in e.strong_concepts])
        weakest = top_concepts([c for e in evs for c in e.missing_concepts])
        feedback = _generate_feedback(avg, strongest, weakest)

        final_summaries.append(
            TopicSummary(
                topic=topic,
                total_questions=n,
                average_score=avg,
                confidence_score=avg_confidence,
                strongest_concepts=strongest,
                weakest_concepts=weakest,
                feedback=feedback,
            )
        )

    # Validate output of deterministic topic summaries
    from app.integration.langGraph.outputValidator import validate_topic_summaries

    val_res = validate_topic_summaries(final_summaries, evaluations)
    if not val_res.is_valid:
        return {
            "errors": [f"topic_aggregation validation failed: {val_res.error_message}"],
            "topic_aggregation_status": ProcessingStatus.FAILED,
        }

    output = {
        "topic_summaries": final_summaries,
        "topic_aggregation_status": ProcessingStatus.COMPLETED,
    }

    logger.info(
        f"[{interview_id}] topic_aggregation OK: topics={len(final_summaries)}, "
        f"names={[t.topic for t in final_summaries]}, "
        f"avg_scores={[t.average_score for t in final_summaries]}"
    )

    return output


# ---------------------------------------------------------------------------
# Node 4 — Interview Summary
# ---------------------------------------------------------------------------


@log_node_execution("interview_summary")
async def interview_summary(state: InterviewGraphState):
    """
    Produces the final InterviewSummary with a HiringDecision.
    """
    evaluations: list[QuestionEvaluation] = state["question_evaluations"]
    topic_summaries: list[TopicSummary] = state["topic_summaries"]
    candidate_name = state.get("candidate_name")
    claimed_experience_years = state.get("claimed_experience_years")
    interview_id = state.get("interview_id", "unknown")

    def mean(vals: list[float]) -> float:
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    technical_score = mean([(e.accuracy_score + e.depth_score + e.completeness_score) / 3 for e in evaluations])
    communication_score = mean([e.clarity_score for e in evaluations])
    confidence_score = mean([e.confidence_score for e in evaluations])
    knowledge_depth = mean([e.depth_score for e in evaluations])
    experience_alignment_score = mean([e.experience_alignment_score for e in evaluations])
    overall_score = mean([technical_score, communication_score, confidence_score, knowledge_depth])

    sorted_topics = sorted(topic_summaries, key=lambda t: t.average_score, reverse=True)
    strongest_topics = [t.topic for t in sorted_topics[:3]]
    weakest_topics = [t.topic for t in sorted_topics[-3:] if t.average_score < 6.0]
    skills_assessed = list({e.category for e in evaluations})

    score_block = (
        f"Candidate: {candidate_name or 'Unknown'}\n"
        f"Claimed experience: {claimed_experience_years or 'N/A'} years\n"
        f"Overall: {overall_score}/10 | Technical: {technical_score}/10 | "
        f"Communication: {communication_score}/10 | Confidence: {confidence_score}/10\n"
        f"Knowledge depth: {knowledge_depth}/10 | "
        f"Experience alignment: {experience_alignment_score}/10\n"
        f"Questions evaluated: {len(evaluations)}\n"
        f"Strongest topics: {', '.join(strongest_topics) or 'none'}\n"
        f"Weakest topics: {', '.join(weakest_topics) or 'none'}"
    )

    topic_block = "\n".join(
        f"- {t.topic} | score: {t.average_score}/10 | confidence: {t.confidence_score}/10 | {t.feedback}"
        for t in topic_summaries
    )

    sorted_evals = sorted(evaluations, key=lambda e: e.accuracy_score)
    notable_weak = sorted_evals[:3]
    notable_strong = sorted_evals[-3:]

    notable_block = "Weakest answers:\n" + "\n".join(
        f"  [{e.question_id}] {e.question[:40]} → accuracy {e.accuracy_score}/10, "
        f"missing: {', '.join(e.missing_concepts[:3])}"
        for e in notable_weak
    )
    notable_block += "\n\nStrongest answers:\n" + "\n".join(
        f"  [{e.question_id}] {e.question[:40]} → accuracy {e.accuracy_score}/10, "
        f"strong: {', '.join(e.strong_concepts[:3])}"
        for e in notable_strong
    )

    payload = {"scores": score_block, "topics": topic_block, "notable": notable_block}

    # Validation retry loop
    max_validation_attempts = 2
    validation_err = None

    for attempt in range(1, max_validation_attempts + 1):
        try:
            result: InterviewSummary = await retry_manager.invoke_structured(
                node_name="interview_summary",
                interview_id=interview_id,
                prompt=INTERVIEW_SUMMARY_CHAT_PROMPT,
                schema=InterviewSummary,
                payload=payload,
            )

            # Apply final deterministic overwrite/pin values
            final = result.model_copy(
                update={
                    "candidate_name": candidate_name,
                    "claimed_experience_years": claimed_experience_years,
                    "overall_score": overall_score,
                    "technical_score": technical_score,
                    "communication_score": communication_score,
                    "confidence_score": confidence_score,
                    "knowledge_depth": knowledge_depth,
                    "experience_alignment_score": experience_alignment_score,
                    "strongest_topics": strongest_topics,
                    "weakest_topics": weakest_topics,
                    "skills_assessed": skills_assessed,
                }
            )

            # Validate output
            from app.integration.langGraph.outputValidator import validate_interview_summary

            val_res = validate_interview_summary(final)
            if val_res.is_valid:
                logger.info(
                    f"[{interview_id}] interview_summary OK: decision={final.hiring_decision}, "
                    f"overall={final.overall_score}, technical={final.technical_score}, "
                    f"skills={final.skills_assessed}, "
                    f"final_feedback_chars={len(final.final_feedback or '')}, "
                    f"strengths={len(final.strengths)}, weaknesses={len(final.weaknesses)}, "
                    f"risk_factors={len(final.risk_factors)}, "
                    f"strongest_topics={final.strongest_topics}, weakest_topics={final.weakest_topics}"
                )
                return {
                    "interview_summary": final,
                    "final_summary_status": ProcessingStatus.COMPLETED,
                }
            else:
                validation_err = val_res.error_message
                logger.warning(
                    f"[{interview_id}] interview_summary validation attempt {attempt} failed: {validation_err}"
                )
        except Exception as e:
            validation_err = str(e)
            logger.warning(f"[{interview_id}] interview_summary attempt {attempt} raised exception: {validation_err}")

    return {
        "errors": [f"interview_summary validation failed: {validation_err}"],
        "final_summary_status": ProcessingStatus.FAILED,
    }
