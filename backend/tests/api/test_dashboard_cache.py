import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.dashboard.cache import (
    clear_user_dashboard_cache,
    invalidate_dashboard_cache_sync,
    overview_cache_key,
    topic_questions_cache_key,
    topic_slug,
)


class TestTopicSlug:
    def test_lowercases_and_hyphenates(self):
        assert topic_slug("System Design") == "system-design"

    def test_multiword_and_punctuation(self):
        assert topic_slug("Python / Cloud & DevOps!") == "python-cloud-devops"

    def test_empty(self):
        assert topic_slug("") == ""


class TestCacheKeys:
    def test_overview_key(self):
        assert overview_cache_key("u1") == "dashboard:overview:u1"

    def test_topic_questions_key(self):
        key = topic_questions_cache_key("u1", "System Design", 50, 20, "score")
        assert key == "dashboard:topic_questions:u1:system-design:50:20:score"


@pytest.mark.asyncio
async def test_clear_user_dashboard_cache_deletes_all_pages():
    class FakeRedis:
        def __init__(self, pages):
            self._pages = pages
            self.deleted = []

        async def delete(self, *keys):
            self.deleted.extend(keys)

        async def scan_iter(self, match):
            for key in self._pages.get(match, []):
                yield key

    pages = {
        "dashboard:topic_questions:u1:system-design:*": [
            "dashboard:topic_questions:u1:system-design:50:0:recent",
        ],
        "dashboard:topic_questions:u1:python:*": [
            "dashboard:topic_questions:u1:python:50:0:recent",
            "dashboard:topic_questions:u1:python:50:0:score",
        ],
    }
    redis = FakeRedis(pages)

    await clear_user_dashboard_cache(redis, "u1", ["System Design", "Python"])

    assert "dashboard:overview:u1" in redis.deleted
    assert "dashboard:topic_questions:u1:system-design:50:0:recent" in redis.deleted
    assert "dashboard:topic_questions:u1:python:50:0:recent" in redis.deleted
    assert "dashboard:topic_questions:u1:python:50:0:score" in redis.deleted


def test_invalidate_dashboard_cache_sync_uses_fresh_client_and_closes():
    fake_client = AsyncMock()

    with (
        patch("redis.asyncio.Redis.from_url", return_value=fake_client) as mock_from_url,
        patch("app.core.config.settings.REDIS_URL", "redis://test:6379/0"),
    ):
        invalidate_dashboard_cache_sync(uuid.uuid4(), ["Python"])

    mock_from_url.assert_called_once()
    fake_client.aclose.assert_awaited_once()


def test_invalidate_dashboard_cache_sync_survives_failures():
    with patch("redis.asyncio.Redis.from_url", side_effect=RuntimeError):
        # Should not raise: cache invalidation is best-effort.
        invalidate_dashboard_cache_sync(uuid.uuid4(), ["Python"])
