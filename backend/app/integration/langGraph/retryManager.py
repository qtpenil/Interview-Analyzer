import asyncio
import random
import time
from typing import Any, ClassVar

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.core.config import settings
from app.integration.langGraph.provider_strategy import provider_manager
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Key resolution — which settings field(s) hold credentials per provider.
# ---------------------------------------------------------------------------

# Primary, comma-separated key pool for each provider (may be empty).
_KEY_POOL_ENV: dict[str, str] = {
    "google": "GEMINI_API_KEYS",
    "openai": "OPENAI_API_KEYS",
    "anthropic": "ANTHROPIC_API_KEYS",
}

# Single-key fallback when no pool is configured (Google has none — its
# "pool" field *is* the list of keys).
_KEY_SINGLE_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


class KeyRotator:
    """Holds the API-key pool for a single provider and rotates through it.

    Rotation is the mechanism by which we (a) distribute load across multiple
    keys on transient errors (rate limits) and (b) skip a single revoked /
    invalid key on hard errors. Callers should rotate after *every* failed
    attempt — see ``RetryManager`` — so a bad key never sinks the whole pool.
    """

    def __init__(self, provider: str):
        self.provider = provider
        self.keys: list[str] = []
        self._current_index = 0
        self._load_keys()

    def _load_keys(self) -> None:
        pool_env = _KEY_POOL_ENV.get(self.provider)
        if pool_env:
            raw = getattr(settings, pool_env, "")
            if raw:
                self.keys = [k.strip() for k in raw.split(",") if k.strip()]

        # Fall back to a single-key setting if the pool was empty.
        if not self.keys:
            single_env = _KEY_SINGLE_ENV.get(self.provider)
            if single_env:
                single = getattr(settings, single_env, "")
                if single:
                    self.keys = [single.strip()]

    @property
    def is_configured(self) -> bool:
        """Whether this provider has at least one usable API key."""
        return bool(self.keys)

    def __len__(self) -> int:
        return len(self.keys)

    def get_current_key(self) -> str | None:
        if not self.keys:
            return None
        return self.keys[self._current_index % len(self.keys)]

    def current_key_index(self) -> int:
        if not self.keys:
            return -1
        return self._current_index % len(self.keys)

    def rotate(self) -> None:
        if len(self.keys) > 1:
            self._current_index = (self._current_index + 1) % len(self.keys)
            logger.info(
                f"Rotated to next API key for provider {self.provider} "
                f"(index: {self._current_index % len(self.keys)})"
            )


def is_transient_exception(exc: Exception) -> bool:
    """
    Check if an exception represents a transient failure that is worth retrying.
    Checks names and properties to support multiple SDKs without strict dependency imports.
    """
    name = type(exc).__name__

    # Core python / asyncio timeout/connection issues
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError, OSError)):
        return True

    # Check for network or timeout signatures in class name
    if "Timeout" in name or "Connection" in name or "Network" in name:
        return True

    # Try to extract HTTP status code
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        # Check standard SDK response structures
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            status_code = body.get("status")
        if status_code is None:
            status_code = getattr(exc, "code", None)

    if isinstance(status_code, int) and (status_code == 429 or status_code >= 500):
        return True

    # SDK-specific rate limit / server error class names
    transient_names = {
        "RateLimitError",
        "InternalServerError",
        "APIConnectionError",
        "APITimeoutError",
        "ResourceExhausted",
        "ServiceUnavailable",
        "DeadlineExceeded",
        "ServerOverloadedError",
    }
    if name in transient_names:
        return True

    # Check exception messages
    msg = str(exc).lower()
    return any(
        term in msg
        for term in [
            "429",
            "rate limit",
            "quota exceeded",
            "503",
            "500",
            "timeout",
            "temporarily unavailable",
            "service unavailable",
        ]
    )


def describe_exception(exc: Exception) -> str:
    """
    Produce a non-empty, diagnosable description of an exception.
    Some SDK exceptions (notably Google's) have an empty str(exc) and stash the
    real detail on attributes like .message / .args / .body, so falling back to
    just str(exc) can silently log nothing useful ("Transient failure: ").
    """
    parts = [type(exc).__name__]

    msg = str(exc).strip()
    if msg:
        parts.append(msg)
    else:
        # Try common alternate locations for the real error detail
        for attr in ("message", "reason"):
            val = getattr(exc, attr, None)
            if val:
                parts.append(str(val))
                break
        else:
            if getattr(exc, "args", None):
                parts.append(str(exc.args))
            body = getattr(exc, "body", None)
            if body:
                parts.append(f"body={body}")
            status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status_code is not None:
                parts.append(f"status={status_code}")

    return ": ".join(parts) if len(parts) > 1 else parts[0] + " (no further detail available)"


def _try_get_metrics():
    """Resolve the active node-metrics tracker without forcing an import cycle."""
    try:
        from app.integration.langGraph.logger_decorator import node_metrics_var

        return node_metrics_var.get()
    except ImportError:
        return None


class RetryManager:
    """
    Centralized executor for structured LLM requests.
    Supports timeouts, exponential backoffs, key rotation, and provider fallbacks.

    Key-rotation contract: on *any* failed attempt (transient or not) we rotate
    to the next key before retrying. A single invalid/revoked key must not abort
    the whole provider — the remaining keys in the pool should still be tried.
    """

    # Providers that are actually allowed to be used right now.
    # Rotators for other providers (openai, anthropic, ollama) are still built
    # below so that re-enabling one later is just adding it to this set --
    # no other code changes needed.
    ACTIVE_PROVIDERS: ClassVar[set[str]] = {"google"}

    def __init__(self):
        self.rotators = {
            "google": KeyRotator("google"),
            "openai": KeyRotator("openai"),
            "anthropic": KeyRotator("anthropic"),
            "ollama": KeyRotator("ollama"),
        }

    # ── Provider selection ───────────────────────────────────────────────────

    def _select_providers(self, interview_id: str) -> list[str]:
        """Return the providers to attempt, restricted to active + configured ones."""
        candidate = [settings.PRIMARY_PROVIDER]
        if (
            settings.ENABLE_PROVIDER_FALLBACK
            and settings.FALLBACK_PROVIDER
            and settings.FALLBACK_PROVIDER != settings.PRIMARY_PROVIDER
        ):
            candidate.append(settings.FALLBACK_PROVIDER)

        providers: list[str] = []
        for provider in candidate:
            if provider not in self.ACTIVE_PROVIDERS:
                logger.info(
                    f"[{interview_id}] Skipping provider '{provider}': not in ACTIVE_PROVIDERS."
                )
                continue
            rotator = self.rotators.get(provider)
            if rotator and rotator.is_configured:
                providers.append(provider)
            else:
                logger.info(
                    f"[{interview_id}] Skipping provider '{provider}': no API key(s) configured."
                )

        return providers

    # ── Chain construction ───────────────────────────────────────────────────

    @staticmethod
    def _build_chain(provider: str, api_key: str | None, prompt: ChatPromptTemplate, schema: type[BaseModel]):
        prov = provider_manager.get_provider(provider)
        model = prov.build_model(api_key=api_key)
        structured_model = model.with_structured_output(schema)
        chain = prompt | structured_model
        return model, chain

    @staticmethod
    def _llm_gate(interview_id: str):
        """Return the async context manager that gates concurrent LLM requests.

        Note: this is intentionally a *synchronous* factory — it returns the
        context manager object, which the caller enters with ``async with``.
        Marking it ``async def`` would return a coroutine instead, which cannot
        be used as an async context manager.
        """
        from app.integration.langGraph.concurrency import get_concurrency_manager

        concurrency_mgr = get_concurrency_manager()
        return concurrency_mgr.gate_llm_request(interview_id)

    # ── Public entry point ───────────────────────────────────────────────────

    async def invoke_structured(
        self,
        node_name: str,
        interview_id: str,
        prompt: ChatPromptTemplate,
        schema: type[BaseModel],
        payload: dict[str, Any],
    ) -> Any:
        """
        Execute structured output chain with full retry budget, key-rotation, and fallbacks.
        """
        providers = self._select_providers(interview_id)

        if not providers:
            raise RuntimeError(
                f"No configured LLM providers available for node '{node_name}' "
                f"(checked: {[settings.PRIMARY_PROVIDER, settings.FALLBACK_PROVIDER]}). "
                f"Set at least one provider's API key(s)."
            )

        last_exception: Exception | None = None

        for provider in providers:
            rotator = self.rotators[provider]
            try:
                return await self._run_provider(node_name, interview_id, prompt, schema, payload, provider, rotator)
            except Exception as exc:
                last_exception = exc
                logger.critical(
                    f"[{interview_id}] All keys/retries exhausted for provider '{provider}'!",
                    extra={
                        "structured": {
                            "interview_id": interview_id,
                            "node_name": node_name,
                            "action": "llm_all_keys_exhausted",
                            "error": describe_exception(exc),
                        }
                    },
                )

        if last_exception is None:
            raise RuntimeError(f"All LLM providers exhausted for node '{node_name}' without an exception")
        raise last_exception

    # ── Per-provider execution ───────────────────────────────────────────────

    async def _run_provider(
        self,
        node_name: str,
        interview_id: str,
        prompt: ChatPromptTemplate,
        schema: type[BaseModel],
        payload: dict[str, Any],
        provider: str,
        rotator: KeyRotator,
    ) -> Any:
        """
        Try every key in the rotator (at least once) for a single provider,
        retrying with exponential backoff. The attempt budget is the larger of
        MAX_RETRIES and the number of keys, so all keys are guaranteed a turn.
        """
        key_count = len(rotator)
        if key_count == 0:
            raise RuntimeError(f"Provider '{provider}' has no configured API keys for node '{node_name}'")

        max_attempts = max(settings.MAX_RETRIES, key_count)

        metrics = _try_get_metrics()
        last_exception: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            api_key = rotator.get_current_key()
            key_index = rotator.current_key_index()

            model, chain = self._build_chain(provider, api_key, prompt, schema)

            logger.info(
                f"[{interview_id}] Starting LLM attempt {attempt}/{max_attempts} for node '{node_name}' "
                f"on '{provider}' (key index {key_index}/{key_count - 1})",
                extra={
                    "structured": {
                        "interview_id": interview_id,
                        "node_name": node_name,
                        "provider": provider,
                        "attempt": attempt,
                        "key_index": key_index,
                        "action": "llm_attempt_start",
                    }
                },
            )

            start_time = time.perf_counter()
            try:
                async with self._llm_gate(interview_id):
                    result = await asyncio.wait_for(chain.ainvoke(payload), timeout=settings.LLM_TIMEOUT_SECONDS)

                elapsed = time.perf_counter() - start_time
                logger.info(
                    f"[{interview_id}] LLM attempt {attempt} succeeded for node '{node_name}' on '{provider}' in {elapsed:.2f}s",
                    extra={
                        "structured": {
                            "interview_id": interview_id,
                            "node_name": node_name,
                            "provider": provider,
                            "attempt": attempt,
                            "elapsed_seconds": elapsed,
                            "outcome": "success",
                            "action": "llm_attempt_success",
                        }
                    },
                )

                if metrics:
                    metrics.provider = provider
                    metrics.model = getattr(model, "model_name", getattr(model, "model", "unknown"))
                    metrics.retries += attempt - 1
                    metrics.prompt_chars += len(str(payload))
                    metrics.response_chars += len(str(result))

                return result

            except Exception as exc:
                elapsed = time.perf_counter() - start_time
                last_exception = exc
                exc_desc = describe_exception(exc)
                transient = is_transient_exception(exc)

                if transient:
                    logger.warning(
                        f"[{interview_id}] Transient failure in attempt {attempt} on '{provider}' key {key_index}: {exc_desc}",
                        extra={
                            "structured": {
                                "interview_id": interview_id,
                                "node_name": node_name,
                                "provider": provider,
                                "attempt": attempt,
                                "elapsed_seconds": elapsed,
                                "outcome": "fail_transient",
                                "error": exc_desc,
                                "action": "llm_attempt_fail",
                            }
                        },
                    )
                else:
                    logger.error(
                        f"[{interview_id}] Failure in attempt {attempt} on '{provider}' key {key_index}: {exc_desc}",
                        extra={
                            "structured": {
                                "interview_id": interview_id,
                                "node_name": node_name,
                                "provider": provider,
                                "attempt": attempt,
                                "elapsed_seconds": elapsed,
                                "outcome": "fail_non_transient",
                                "error": exc_desc,
                                "action": "llm_attempt_fail",
                            }
                        },
                    )

                # Rotate before the next attempt so a bad/revoked key is skipped
                # rather than immediately aborting the whole provider.
                rotator.rotate()

                if attempt < max_attempts:
                    backoff = self._compute_backoff(attempt)
                    logger.info(
                        f"[{interview_id}] Backing off for {backoff:.2f}s before next attempt "
                        f"for node '{node_name}' on '{provider}' (now key index {rotator.current_key_index()})",
                        extra={
                            "structured": {
                                "interview_id": interview_id,
                                "node_name": node_name,
                                "backoff_seconds": backoff,
                                "action": "llm_backoff",
                            }
                        },
                    )
                    await asyncio.sleep(backoff)

        if last_exception is None:
            raise RuntimeError(f"Provider '{provider}' failed without an exception for node '{node_name}'")
        raise last_exception

    @staticmethod
    def _compute_backoff(attempt: int) -> float:
        backoff = min(
            settings.MAX_RETRY_DELAY,
            settings.INITIAL_RETRY_DELAY * (settings.BACKOFF_MULTIPLIER ** (attempt - 1)),
        )
        if settings.ENABLE_RETRY_JITTER:
            backoff = backoff * (0.5 + random.random() * 0.5)
        return backoff


retry_manager = RetryManager()
