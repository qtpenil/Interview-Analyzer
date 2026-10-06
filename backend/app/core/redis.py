from redis.asyncio import Redis

from app.core.config import settings


class _LazyRedis:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client

    def __getattr__(self, name):
        return getattr(self._get_client(), name)


redis_client = _LazyRedis()
