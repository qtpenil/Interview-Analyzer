import abc
import asyncio
import json
import threading
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, cast

from redis.asyncio import Redis

from app.core.config import settings
from app.integration.langGraph.Schema.assessmentSchema import (
    InterviewSummary,
    QuestionEvaluation,
    TopicSummary,
)

# Import schema classes for deserialization
from app.integration.langGraph.Schema.interviewSchema import ConversationBlock, QuestionAnswer
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# State Serialization Helpers for Checkpointing
# ---------------------------------------------------------------------------


def serialize_state(state: dict[str, Any]) -> str:
    """Helper to convert LangGraph state dict with datetimes/pydantic models to JSON."""
    serialized: dict[str, Any] = {}
    for k, v in state.items():
        if isinstance(v, datetime):
            serialized[k] = {"__type__": "datetime", "value": v.isoformat()}
        elif hasattr(v, "model_dump"):
            serialized[k] = {"__type__": type(v).__name__, "value": v.model_dump()}
        elif isinstance(v, list):
            serialized_list = []
            for item in v:
                if hasattr(item, "model_dump"):
                    serialized_list.append({"__type__": type(item).__name__, "value": item.model_dump()})
                else:
                    serialized_list.append(item)
            serialized[k] = serialized_list
        else:
            serialized[k] = v
    return json.dumps(serialized)


def deserialize_state(state_str: str) -> dict[str, Any]:
    """Helper to restore custom schemas and datetime objects from a JSON string."""
    data = json.loads(state_str)
    deserialized: dict[str, Any] = {}

    type_mapping = {
        "ConversationBlock": ConversationBlock,
        "QuestionAnswer": QuestionAnswer,
        "QuestionEvaluation": QuestionEvaluation,
        "TopicSummary": TopicSummary,
        "InterviewSummary": InterviewSummary,
    }

    for k, v in data.items():
        if isinstance(v, dict) and v.get("__type__") == "datetime":
            deserialized[k] = datetime.fromisoformat(v["value"])
        elif isinstance(v, dict) and v.get("__type__") in type_mapping:
            cls = type_mapping[v["__type__"]]
            deserialized[k] = cls(**v["value"])
        elif isinstance(v, list):
            deserialized_list = []
            for item in v:
                if isinstance(item, dict) and item.get("__type__") in type_mapping:
                    cls = type_mapping[item["__type__"]]
                    deserialized_list.append(cls(**item["value"]))
                else:
                    deserialized_list.append(item)
            deserialized[k] = deserialized_list
        else:
            deserialized[k] = v

    return deserialized


class ConcurrencyTimeoutError(Exception):
    """Raised when a task waits longer than the timeout to acquire a concurrency permit."""

    def __init__(self, limit_type: str, waited_seconds: float, interview_id: str):
        super().__init__(
            f"Concurrency limit reached for {limit_type}. "
            f"Waited {waited_seconds} seconds for interview {interview_id} before timeout."
        )
        self.limit_type = limit_type
        self.waited_seconds = waited_seconds
        self.interview_id = interview_id


class ConcurrencyBackend(abc.ABC):
    """Abstract interface for concurrency coordination and state checkpointing."""

    @abc.abstractmethod
    async def acquire(self, key: str, limit: int, timeout: float, ttl: float) -> str | None:
        """
        Acquire a permit.
        Returns:
            A unique token string if acquired successfully, or None if timed out.
        """
        pass

    @abc.abstractmethod
    async def release(self, key: str, token: str) -> None:
        """Release the permit matching the token."""
        pass

    @abc.abstractmethod
    async def set_checkpoint(self, key: str, state: dict[str, Any]) -> None:
        """Persist a state checkpoint."""
        pass

    @abc.abstractmethod
    async def get_checkpoint(self, key: str) -> dict[str, Any] | None:
        """Retrieve a persisted state checkpoint."""
        pass


# ---------------------------------------------------------------------------
# Local/In-Process Implementation
# ---------------------------------------------------------------------------


class LocalSemaphore:
    """A threading-lock-based semaphore safe across asyncio.run() boundaries."""

    def __init__(self, limit: int):
        self.limit = limit
        self.current = 0
        self.lock = threading.Lock()
        self.active_tokens: set[str] = set()

    def acquire(self, token: str) -> bool:
        with self.lock:
            if self.current < self.limit:
                self.current += 1
                self.active_tokens.add(token)
                return True
            return False

    def release(self, token: str) -> None:
        with self.lock:
            if token in self.active_tokens:
                self.active_tokens.remove(token)
                self.current = max(0, self.current - 1)


class LocalConcurrencyBackend(ConcurrencyBackend):
    """
    Local process-level concurrency manager.
    Guarantees event-loop safety by avoiding asyncio.Semaphore and using threading locks
    combined with cooperative asyncio.sleep.
    """

    _semaphores: dict[str, LocalSemaphore] = {}
    _checkpoints: dict[str, str] = {}
    _lock = threading.Lock()

    def _get_semaphore(self, key: str, limit: int) -> LocalSemaphore:
        with self._lock:
            if key not in self._semaphores:
                self._semaphores[key] = LocalSemaphore(limit)
            return self._semaphores[key]

    async def acquire(self, key: str, limit: int, timeout: float, ttl: float) -> str | None:
        sem = self._get_semaphore(key, limit)
        token = str(uuid.uuid4())
        start_time = time.perf_counter()

        while True:
            if sem.acquire(token):
                return token

            elapsed = time.perf_counter() - start_time
            if elapsed >= timeout:
                return None

            await asyncio.sleep(0.1)

    async def release(self, key: str, token: str) -> None:
        with self._lock:
            sem = self._semaphores.get(key)
        if sem:
            sem.release(token)

    async def set_checkpoint(self, key: str, state: dict[str, Any]) -> None:
        # Serialize to catch any early serialization issues
        serialized = serialize_state(state)
        with self._lock:
            self._checkpoints[key] = serialized

    async def get_checkpoint(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            serialized = self._checkpoints.get(key)
        if serialized:
            return deserialize_state(serialized)
        return None


# ---------------------------------------------------------------------------
# Redis Distributed Implementation
# ---------------------------------------------------------------------------

_redis_client = None
_redis_loop = None


def get_redis_client() -> Redis:
    """
    Helper to return a Redis client.
    Re-creates the client if the event loop changes to prevent loop-binding bugs.
    """
    global _redis_client, _redis_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # Outside of an active loop (e.g. sync celery worker bootstrap)
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)

    if _redis_client is None or _redis_loop != current_loop:
        logger.info("Initializing new loop-safe Redis client instance.")
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_loop = current_loop
    return _redis_client


class RedisConcurrencyBackend(ConcurrencyBackend):
    """
    Redis-based distributed concurrency manager.
    Uses Lua scripts for atomic sliding-window rate limiting and auto-expiring tokens.
    """

    ACQUIRE_SCRIPT = """
    local semaphore_key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local token = ARGV[2]
    local now = tonumber(ARGV[3])
    local ttl = tonumber(ARGV[4])

    -- clean up expired tokens
    redis.call('zremrangebyscore', semaphore_key, '-inf', now)

    -- check current count
    local count = redis.call('zcard', semaphore_key)
    if count < limit then
        redis.call('zadd', semaphore_key, now + ttl, token)
        return 1
    else
        return 0
    end
    """

    RELEASE_SCRIPT = """
    local semaphore_key = KEYS[1]
    local token = ARGV[1]
    return redis.call('zrem', semaphore_key, token)
    """

    async def acquire(self, key: str, limit: int, timeout: float, ttl: float) -> str | None:
        redis_client = get_redis_client()
        token = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Load Lua scripts
        acquire_sha = await redis_client.script_load(self.ACQUIRE_SCRIPT)

        while True:
            now = int(time.time())
            try:
                res = await redis_client.evalsha(acquire_sha, 1, key, limit, token, now, ttl)
                if res == 1:
                    return token
            except Exception as e:
                # If script is lost/missing or evalsha fails, fall back to eval
                logger.warning(f"evalsha failed for concurrency script, falling back to eval: {e}")
                res = await redis_client.eval(self.ACQUIRE_SCRIPT, 1, key, limit, token, now, ttl)
                if res == 1:
                    return token

            elapsed = time.perf_counter() - start_time
            if elapsed >= timeout:
                return None

            await asyncio.sleep(0.1)

    async def release(self, key: str, token: str) -> None:
        redis_client = get_redis_client()
        try:
            await redis_client.eval(self.RELEASE_SCRIPT, 1, key, token)
        except Exception as e:
            logger.error(f"Failed to release Redis concurrency token: {e}")

    async def set_checkpoint(self, key: str, state: dict[str, Any]) -> None:
        redis_client = get_redis_client()
        serialized = serialize_state(state)
        # Store checkpoint with a 1-day expiration safety margin
        await redis_client.set(key, serialized, ex=86400)

    async def get_checkpoint(self, key: str) -> dict[str, Any] | None:
        redis_client = get_redis_client()
        serialized = await redis_client.get(key)
        if serialized:
            return deserialize_state(cast(str, serialized))
        return None


# ---------------------------------------------------------------------------
# Concurrency Manager Context Interface
# ---------------------------------------------------------------------------


class ConcurrencyManager:
    """Wraps the configured concurrency backend to provide clean context managers."""

    def __init__(self):
        backend_type = settings.CONCURRENCY_BACKEND.lower()
        if backend_type == "redis":
            logger.info("ConcurrencyManager: Using REDIS backend")
            self.backend = RedisConcurrencyBackend()
        else:
            logger.info("ConcurrencyManager: Using LOCAL in-process backend")
            self.backend = LocalConcurrencyBackend()

    @asynccontextmanager
    async def gate_interview(self, interview_id: str) -> AsyncIterator[None]:
        key = "concurrency:interviews"
        limit = settings.MAX_CONCURRENT_INTERVIEWS
        timeout = settings.QUEUE_WAIT_TIMEOUT
        ttl = 3600  # 1 hour safety net

        token = await self.backend.acquire(key, limit, timeout, ttl)
        if not token:
            logger.error(f"[{interview_id}] ConcurrencyTimeoutError for interview limit.")
            raise ConcurrencyTimeoutError("max_concurrent_interviews", timeout, interview_id)

        try:
            yield
        finally:
            await self.backend.release(key, token)

    @asynccontextmanager
    async def gate_llm_request(self, interview_id: str) -> AsyncIterator[None]:
        key = "concurrency:llm"
        limit = settings.MAX_CONCURRENT_LLM_REQUESTS
        timeout = settings.QUEUE_WAIT_TIMEOUT
        ttl = 300  # 5 minutes safety net

        token = await self.backend.acquire(key, limit, timeout, ttl)
        if not token:
            logger.error(f"[{interview_id}] ConcurrencyTimeoutError for LLM request limit.")
            raise ConcurrencyTimeoutError("max_concurrent_llm_requests", timeout, interview_id)

        try:
            yield
        finally:
            await self.backend.release(key, token)


# Global singleton instance resolved at runtime
_concurrency_manager = None
_mgr_lock = threading.Lock()


def get_concurrency_manager() -> ConcurrencyManager:
    global _concurrency_manager
    if _concurrency_manager is None:
        with _mgr_lock:
            if _concurrency_manager is None:
                _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager
