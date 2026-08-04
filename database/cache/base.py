import json
from typing import Any

from .redis_conf import redis_client


class CacheService:
    @staticmethod
    async def set(key: str, value: dict, expire: int | None = None) -> None:
        serialized = json.dumps(value, default=str)
        await redis_client.set(key, serialized, ex=expire)

    @staticmethod
    async def get(key: str) -> dict | None:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    async def delete(key: str) -> None:
        await redis_client.delete(key)

    @staticmethod
    async def scan_keys(pattern: str) -> list[str]:
        keys: list[str] = []
        cursor = 0
        while True:
            cursor, batch = await redis_client.scan(cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys
