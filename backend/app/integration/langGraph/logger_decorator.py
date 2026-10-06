import contextvars
import functools
import time
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.integration.langGraph.Schema.commonSchema import ProcessingStatus
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


# Context variable to aggregate LLM metrics across attempts within a node
class NodeMetrics:
    def __init__(self):
        self.provider = "unknown"
        self.model = "unknown"
        self.retries = 0
        self.prompt_tokens = 0
        self.response_tokens = 0
        self.prompt_chars = 0
        self.response_chars = 0


node_metrics_var: contextvars.ContextVar[NodeMetrics | None] = contextvars.ContextVar("node_metrics", default=None)

NODE_STATUS_KEYS = {
    "transcript_structuring": "transcript_processing_status",
    "metadata_qa_extractor": "metadata_extraction_status",
    "batched_qa_assessment": "assessment_status",
    "topic_aggregation": "topic_aggregation_status",
    "interview_summary": "final_summary_status",
}


# Simple cost estimation based on characters if tokens aren't available,
# or token estimates.
def estimate_cost(provider: str, model: str, prompt_chars: int, response_chars: int) -> float:
    # 1 token is approx 4 characters
    p_tokens = prompt_chars / 4
    r_tokens = response_chars / 4

    provider = provider.lower()
    if "google" in provider:
        # e.g., gemini-1.5-flash: $0.075 per 1M input, $0.30 per 1M output
        return (p_tokens * 0.075 / 1_000_000) + (r_tokens * 0.30 / 1_000_000)
    elif "openai" in provider:
        # e.g., gpt-4o-mini: $0.150 per 1M input, $0.600 per 1M output
        return (p_tokens * 0.15 / 1_000_000) + (r_tokens * 0.60 / 1_000_000)
    elif "anthropic" in provider:
        # e.g. claude-3-5-haiku: $1.00 per 1M input, $5.00 per 1M output
        return (p_tokens * 1.00 / 1_000_000) + (r_tokens * 5.00 / 1_000_000)
    return 0.0


def log_node_execution(node_name: str):
    """
    Decorator for pipeline node functions.
    Automates logging, metrics tracking, failure resilience, and checkpointer persistence.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state: Any, *args, **kwargs) -> dict[str, Any]:
            interview_id = state.get("interview_id", "unknown")
            status_key = NODE_STATUS_KEYS.get(node_name, "status")

            # Check if previous nodes failed
            existing_errors = state.get("errors") or []
            if existing_errors:
                logger.warning(
                    f"[{interview_id}] Skipping node '{node_name}' due to existing errors in state.",
                    extra={
                        "structured": {
                            "interview_id": interview_id,
                            "node_name": node_name,
                            "action": "node_skip_due_to_prior_error",
                        }
                    },
                )
                return {status_key: ProcessingStatus.FAILED}

            # Phase 6: Resume support. If already COMPLETED, skip.
            if state.get(status_key) == ProcessingStatus.COMPLETED:
                logger.info(
                    f"[{interview_id}] Node '{node_name}' already completed in previous run. Skipping.",
                    extra={
                        "structured": {
                            "interview_id": interview_id,
                            "node_name": node_name,
                            "action": "node_skip_already_completed",
                        }
                    },
                )
                return {}

            # Start tracking metrics for this node
            metrics = NodeMetrics()
            token = node_metrics_var.set(metrics)

            start_time = datetime.utcnow()
            start_perf = time.perf_counter()

            logger.info(
                f"[{interview_id}] Entering node '{node_name}'",
                extra={
                    "structured": {
                        "interview_id": interview_id,
                        "node_name": node_name,
                        "execution_start_timestamp": start_time.isoformat(),
                        "action": "node_enter",
                    }
                },
            )

            try:
                # Call original node function
                result = await func(state, *args, **kwargs)

                # Check if the node output returned a failure status
                if result.get(status_key) == ProcessingStatus.FAILED:
                    raise ValueError(result.get("errors", ["Unknown node error"])[-1])

                duration = time.perf_counter() - start_perf
                end_time = datetime.utcnow()

                # Calculate estimated cost
                est_cost = estimate_cost(metrics.provider, metrics.model, metrics.prompt_chars, metrics.response_chars)

                # Extract contextual attributes for logging
                q_count = None
                if node_name == "batched_qa_assessment":
                    q_count = len(result.get("question_evaluations") or state.get("question_evaluations") or [])
                elif node_name == "metadata_qa_extractor":
                    q_count = len(result.get("question_answers") or [])

                log_extra = {
                    "interview_id": interview_id,
                    "node_name": node_name,
                    "execution_start_timestamp": start_time.isoformat(),
                    "execution_end_timestamp": end_time.isoformat(),
                    "duration_seconds": duration,
                    "provider": metrics.provider,
                    "model": metrics.model,
                    "retries_consumed": metrics.retries,
                    "estimated_prompt_tokens": int(metrics.prompt_chars / 4),
                    "estimated_response_tokens": int(metrics.response_chars / 4),
                    "estimated_cost_usd": est_cost,
                    "action": "node_exit_success",
                }
                if q_count is not None:
                    log_extra["question_count"] = q_count

                logger.info(
                    f"[{interview_id}] Node '{node_name}' execution succeeded in {duration:.2f}s",
                    extra={"structured": log_extra},
                )

                # Phase 6: Checkpoint the updated state if enabled
                if settings.ENABLE_CHECKPOINTING:
                    try:
                        # Construct updated state dictionary to persist
                        updated_state = {**state, **result}
                        # Remove keys that shouldn't be serialized or are empty
                        updated_state.pop("raw_transcript", None)  # Do not store raw transcript in checkpoints

                        from app.integration.langGraph.concurrency import get_concurrency_manager

                        concurrency_mgr = get_concurrency_manager()

                        # Store checkpoint in concurrency backend
                        checkpoint_key = f"checkpoint:{interview_id}"
                        # In concurrency backend we can add get_checkpoint / set_checkpoint
                        # Let's verify we add these methods to Backend classes next
                        if hasattr(concurrency_mgr.backend, "set_checkpoint"):
                            await concurrency_mgr.backend.set_checkpoint(checkpoint_key, updated_state)
                            logger.info(f"[{interview_id}] Checkpoint saved successfully for node '{node_name}'")
                    except Exception as chk_exc:
                        logger.error(f"[{interview_id}] Failed to save checkpoint: {chk_exc}")

                return result

            except Exception as exc:
                duration = time.perf_counter() - start_perf
                end_time = datetime.utcnow()

                logger.error(
                    f"[{interview_id}] Node '{node_name}' execution failed after {duration:.2f}s: {exc}",
                    extra={
                        "structured": {
                            "interview_id": interview_id,
                            "node_name": node_name,
                            "execution_start_timestamp": start_time.isoformat(),
                            "execution_end_timestamp": end_time.isoformat(),
                            "duration_seconds": duration,
                            "provider": metrics.provider,
                            "model": metrics.model,
                            "retries_consumed": metrics.retries,
                            "failure_reason": str(exc),
                            "action": "node_exit_fail",
                        }
                    },
                )

                # Return failure status and error log
                return {
                    status_key: ProcessingStatus.FAILED,
                    "errors": existing_errors + [f"Node '{node_name}' failed: {exc}"],
                }

            finally:
                node_metrics_var.reset(token)

        return wrapper

    return decorator
