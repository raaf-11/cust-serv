from __future__ import annotations

import asyncio
import time
from typing import Callable


class TokenBucket:
    def __init__(
        self,
        capacity: float,
        period_s: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.capacity = float(capacity)
        self.rate = self.capacity / period_s
        self._clock = clock
        self._tokens = self.capacity
        self._updated = clock()

    def _refill(self) -> None:
        now = self._clock()
        self._tokens = min(
            self.capacity, self._tokens + (now - self._updated) * self.rate
        )
        self._updated = now

    def wait_time(self, n: float) -> float:
        self._refill()
        n = min(n, self.capacity)
        if self._tokens >= n - 1e-6:
            return 0.0
        return (n - self._tokens) / self.rate

    def consume(self, n: float) -> None:
        self._refill()
        self._tokens -= n

    def refund(self, n: float) -> None:
        self._refill()
        self._tokens = min(self.capacity, self._tokens + n)

    def block_for(self, seconds: float) -> None:
        self._refill()
        self._tokens = min(self._tokens, -self.rate * seconds)


class LLMRateLimiter:
    def __init__(
        self,
        requests_per_minute: int,
        tokens_per_minute: int,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], "asyncio.Future"] = asyncio.sleep,
    ):
        self.requests = TokenBucket(requests_per_minute, 60.0, clock)
        self.tokens = TokenBucket(tokens_per_minute, 60.0, clock)
        self._sleep = sleep
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int) -> float:
        waited = 0.0
        async with self._lock:
            while True:
                delay = max(
                    self.requests.wait_time(1),
                    self.tokens.wait_time(estimated_tokens),
                )
                if delay <= 0:
                    break
                await self._sleep(delay)
                waited += delay

            self.requests.consume(1)
            self.tokens.consume(estimated_tokens)

        return waited

    def record_actual(self, estimated_tokens: int, actual_tokens: int | None) -> None:
        if actual_tokens is None:
            return
        diff = actual_tokens - estimated_tokens
        if diff > 0:
            self.tokens.consume(diff)
        elif diff < 0:
            self.tokens.refund(-diff)

    def penalise(self, seconds: float) -> None:
        self.requests.block_for(seconds)
        self.tokens.block_for(seconds)


def estimate_tokens(messages: list[dict], max_completion_tokens: int = 512) -> int:
    chars = sum(len(m.get("content") or "") for m in messages)
    return chars // 4 + 20 * len(messages) + max_completion_tokens


def _build_default() -> LLMRateLimiter:
    try:
        from app.core.config import settings

        rpm = settings.LLM_REQUESTS_PER_MINUTE
        tpm = settings.LLM_TOKENS_PER_MINUTE
    except Exception:
        rpm, tpm = 25, 5000
    return LLMRateLimiter(rpm, tpm)


llm_rate_limiter = _build_default()
