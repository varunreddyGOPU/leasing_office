"""Redis fixed-window rate limiter. Fails open when Redis is unreachable so
local dev and tests don't require it."""
from __future__ import annotations

import redis
from fastapi import HTTPException, Request

from app.config import settings

_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.redis_url, socket_connect_timeout=0.5, socket_timeout=0.5
        )
    return _client


def rate_limit(bucket: str, per_minute: int):
    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{bucket}:{ip}"
        try:
            count = _redis().incr(key)
            if count == 1:
                _redis().expire(key, 60)
        except redis.RedisError:
            return  # fail open
        if count > per_minute:
            raise HTTPException(status_code=429, detail="Too many requests — please try again in a minute.")

    return dependency
