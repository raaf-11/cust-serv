from __future__ import annotations

import math
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, Request, Response, status


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_s: float


class InMemoryBackend:
    _SWEEP_EVERY = 1000

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._windows: dict[str, float] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, key: str, limit: int, window_s: float) -> RateLimitResult:
        now = self._clock()

        with self._lock:
            self._calls += 1
            if self._calls % self._SWEEP_EVERY == 0:
                self._sweep(now)

            q = self._hits.setdefault(key, deque())
            self._windows[key] = window_s

            while q and q[0] <= now - window_s:
                q.popleft()

            if len(q) >= limit:
                retry_after = q[0] + window_s - now
                return RateLimitResult(False, limit, 0, max(retry_after, 0.0))

            q.append(now)
            return RateLimitResult(True, limit, limit - len(q), 0.0)

    def _sweep(self, now: float) -> None:
        for key in list(self._hits):
            q = self._hits[key]
            if not q or q[-1] <= now - self._windows.get(key, 0):
                del self._hits[key]
                self._windows.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._windows.clear()


class RedisBackend:
    def __init__(self, url: str):
        import redis

        self._r = redis.Redis.from_url(url)

    def hit(self, key: str, limit: int, window_s: float) -> RateLimitResult:
        now = time.time()
        rkey = f"ratelimit:{key}"
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(rkey, 0, now - window_s)
        pipe.zcard(rkey)
        pipe.zrange(rkey, 0, 0, withscores=True)
        _, count, oldest = pipe.execute()

        if count >= limit:
            oldest_ts = oldest[0][1] if oldest else now
            return RateLimitResult(
                False, limit, 0, max(oldest_ts + window_s - now, 0.0)
            )

        pipe = self._r.pipeline()
        pipe.zadd(rkey, {f"{now}:{uuid.uuid4().hex}": now})
        pipe.expire(rkey, int(math.ceil(window_s)) + 1)
        pipe.execute()
        return RateLimitResult(True, limit, limit - count - 1, 0.0)

    def reset(self) -> None:
        for k in self._r.scan_iter("ratelimit:*"):
            self._r.delete(k)


def _build_backend():
    try:
        from app.core.config import settings

        url = getattr(settings, "REDIS_URL", None)
    except Exception:
        url = None

    if url:
        try:
            backend = RedisBackend(url)
            print("RateLimiter: using Redis backend")
            return backend
        except Exception as e:
            print("RateLimiter: Redis unavailable, falling back to memory:", repr(e))

    return InMemoryBackend()


backend = _build_backend()


def _enabled() -> bool:
    try:
        from app.core.config import settings

        return settings.RATE_LIMIT_ENABLED
    except Exception:
        return True


def client_ip(request: Request) -> str:
    try:
        from app.core.config import settings

        trust = settings.TRUST_PROXY_HEADERS
    except Exception:
        trust = False

    if trust:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def _enforce(key: str, rules: list[tuple[int, float]], response: Response) -> None:
    tightest_remaining = None
    tightest_limit = None

    for limit, window_s in rules:
        result = backend.hit(f"{key}:{limit}/{int(window_s)}s", limit, window_s)

        if not result.allowed:
            retry = int(math.ceil(result.retry_after_s)) or 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "You're sending messages too quickly. "
                    f"Please wait {retry} second{'s' if retry != 1 else ''} and try again."
                ),
                headers={
                    "Retry-After": str(retry),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        if tightest_remaining is None or result.remaining < tightest_remaining:
            tightest_remaining = result.remaining
            tightest_limit = limit

    if tightest_limit is not None:
        response.headers["X-RateLimit-Limit"] = str(tightest_limit)
        response.headers["X-RateLimit-Remaining"] = str(tightest_remaining)


def limit_by_ip(name: str, *rules: tuple[int, float]):
    def dependency(request: Request, response: Response) -> None:
        if _enabled():
            _enforce(f"{name}:ip:{client_ip(request)}", list(rules), response)

    return dependency


def limit_by_user(name: str, *rules: tuple[int, float]):
    from app.dependencies.auth import get_current_user

    def dependency(response: Response, current_user=Depends(get_current_user)) -> None:
        if _enabled():
            _enforce(f"{name}:user:{current_user.id}", list(rules), response)

    return dependency
