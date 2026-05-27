import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


class RedisCache:
    def __init__(self, prefix: str = "opsmind"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        r = await get_redis()
        val = await r.get(self._key(key))
        return json.loads(val) if val else None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        r = await get_redis()
        await r.setex(self._key(key), ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        r = await get_redis()
        await r.delete(self._key(key))

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        r = await get_redis()
        await r.publish(channel, json.dumps(message, default=str))

    async def lpush(self, key: str, value: Any, max_len: int = 10_000) -> None:
        r = await get_redis()
        pipe = r.pipeline()
        pipe.lpush(self._key(key), json.dumps(value, default=str))
        pipe.ltrim(self._key(key), 0, max_len - 1)
        await pipe.execute()

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        r = await get_redis()
        items = await r.lrange(self._key(key), start, end)
        return [json.loads(i) for i in items]


cache = RedisCache()