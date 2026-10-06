from __future__ import annotations

import asyncio
import re
from collections.abc import Iterable

from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


def topic_slug(topic: str) -> str:
    """Normalize a topic name into a safe cache-key slug, e.g. "System Design" -> "system-design"."""
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower())
    return slug.strip("-")


def overview_cache_key(user_id) -> str:
    return f"dashboard:overview:{user_id}"


def topic_questions_cache_key(user_id, topic: str, limit: int, offset: int, sort: str) -> str:
    return f"dashboard:topic_questions:{user_id}:{topic_slug(topic)}:{limit}:{offset}:{sort}"


async def clear_user_dashboard_cache(redis, user_id, topics: Iterable[str]) -> None:
    """Delete the overview key + topic-question pages for the given topics."""
    await redis.delete(overview_cache_key(user_id))
    for topic in topics:
        pattern = f"dashboard:topic_questions:{user_id}:{topic_slug(topic)}:*"
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)


def invalidate_dashboard_cache_sync(user_id, topics: Iterable[str]) -> None:
    """
    Best-effort sync entry point used from Celery tasks (no running event loop).

    Uses a fresh async Redis client per call so connections never get bound to a
    closed event loop. Failures are logged and swallowed — cache invalidation
    must never take the analysis pipeline down.
    """
    from redis.asyncio import Redis as AsyncRedis

    from app.core.config import settings

    async def _run() -> None:
        client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await clear_user_dashboard_cache(client, user_id, topics)
        finally:
            try:
                await client.aclose()
            except (AttributeError, NotImplementedError):  # pragma: no cover - redis-py version variance
                await client.close()

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(_run())
        except Exception as exc:  # pragma: no cover - cache is best-effort
            logger.warning(f"Dashboard cache invalidation failed for user {user_id}: {exc}")
    else:  # pragma: no cover - used only when invoked from within an event loop (tests)
        logger.warning(f"Dashboard cache invalidation skipped for user {user_id}: running inside an event loop")
