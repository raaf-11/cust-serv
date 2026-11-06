"""
Outbound rate limiting for the LLM provider (Groq).

Groq enforces per-model limits on requests/minute (RPM) and
tokens/minute (TPM). Going over returns HTTP 429, which used to surface as
"I'm currently unavailable" for the customer and as fake failures in the
eval. Two layers fix that:

1. Client-side throttle (this module): two token buckets, one for requests
   and one for tokens. Before each call we wait until both have capacity,
   so bursts get *queued* instead of rejected. After the call, the bucket is
   corrected with the real token count from the response's `usage` field.

2. Retry with backoff (llm_service.post_chat_completion): if a 429/5xx still
   happens (other process using the same key, estimate too low), honour the
   provider's Retry-After header, otherwise exponential backoff + jitter.

Process-local by design: one uvicorn worker = one bucket. With several
workers, divide the limits by the worker count.
"""

from __future__ import annotations

import asyncio
import time
from typing import Callable


class TokenBucket:
    """
    Classic token bucket: holds up to `capacity` tokens, refills at
    `capacity / period_s` per second. `take(n)` waits until n are available.
    """

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
        """Seconds until n tokens are available (0 if available now)."""
        self._refill()
        n = min(n, self.capacity)  # a single huge request must still be able to run
        # Small tolerance: after sleeping exactly the computed delay, float
        # rounding can leave us 1e-12 short, which would otherwise loop
        # forever on ever-tinier sleeps.
        if self._tokens >= n - 1e-6:
            return 0.0
        return (n - self._tokens) / self.rate

    def consume(self, n: float) -> None:
        self._refill()
        self._tokens -= n  # may go negative when correcting with real usage

    def refund(self, n: float) -> None:
        self._refill()
        self._tokens = min(self.capacity, self._tokens + n)

    def block_for(self, seconds: float) -> None:
        """Empty the bucket so nothing can be taken for `seconds`."""
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
        """
        Wait until a request of ~estimated_tokens fits under both limits,
        then reserve it. Returns how long we waited (for logging/metrics).
        Callers are served in arrival order (the lock is FIFO).
        """

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
        """Fix up the token bucket once we know the real usage."""
        if actual_tokens is None:
            return
        diff = actual_tokens - estimated_tokens
        if diff > 0:
            self.tokens.consume(diff)
        elif diff < 0:
            self.tokens.refund(-diff)

    def penalise(self, seconds: float) -> None:
        """
        The provider said "slow down for N seconds": drain both buckets so
        every queued caller waits too, instead of all retrying at once.
        """
        self.requests.block_for(seconds)
        self.tokens.block_for(seconds)


def estimate_tokens(messages: list[dict], max_completion_tokens: int = 512) -> int:
    """
    Cheap estimate (~4 characters per token for English) of prompt tokens,
    plus room for the completion. Only used for throttling, so being a bit
    off is fine - record_actual() corrects it afterwards.
    """
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
