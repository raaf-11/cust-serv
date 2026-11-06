"""
Unit tests for both rate limiters. No services, no network:

    pytest tests/test_rate_limiter.py -q
"""

import asyncio

import pytest
from fastapi import HTTPException, Response

from app.core import rate_limiter
from app.core.rate_limiter import InMemoryBackend
from app.services.llm_rate_limiter import LLMRateLimiter, TokenBucket, estimate_tokens


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


# ---------------------------------------------------------------------------
# Inbound sliding window
# ---------------------------------------------------------------------------

def test_allows_up_to_limit_then_blocks():
    clock = FakeClock()
    b = InMemoryBackend(clock=clock)
    results = [b.hit("k", 3, 60) for _ in range(4)]
    assert [r.allowed for r in results] == [True, True, True, False]
    assert results[2].remaining == 0
    assert results[3].retry_after_s == pytest.approx(60)


def test_window_slides():
    clock = FakeClock()
    b = InMemoryBackend(clock=clock)
    b.hit("k", 2, 60)
    clock.advance(30)
    b.hit("k", 2, 60)
    assert not b.hit("k", 2, 60).allowed
    clock.advance(30.1)  # first hit has left the window, second hasn't
    assert b.hit("k", 2, 60).allowed
    assert not b.hit("k", 2, 60).allowed


def test_no_fixed_window_boundary_burst():
    # A fixed "per calendar minute" counter would allow 2x the limit across
    # a minute boundary. The sliding window must not.
    clock = FakeClock()
    b = InMemoryBackend(clock=clock)
    clock.advance(59)
    assert all(b.hit("k", 5, 60).allowed for _ in range(5))
    clock.advance(2)
    assert not b.hit("k", 5, 60).allowed


def test_keys_are_independent():
    b = InMemoryBackend(clock=FakeClock())
    assert b.hit("user:1", 1, 60).allowed
    assert not b.hit("user:1", 1, 60).allowed
    assert b.hit("user:2", 1, 60).allowed


def test_enforce_raises_429_with_retry_after(monkeypatch):
    monkeypatch.setattr(rate_limiter, "backend", InMemoryBackend(clock=FakeClock()))
    resp = Response()
    rate_limiter._enforce("chat:user:7", [(2, 60)], resp)
    assert resp.headers["X-RateLimit-Remaining"] == "1"
    rate_limiter._enforce("chat:user:7", [(2, 60)], Response())

    with pytest.raises(HTTPException) as exc:
        rate_limiter._enforce("chat:user:7", [(2, 60)], Response())

    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == "60"


def test_tightest_of_several_rules_wins(monkeypatch):
    monkeypatch.setattr(rate_limiter, "backend", InMemoryBackend(clock=FakeClock()))
    rules = [(10, 60), (3, 3600)]
    for _ in range(3):
        rate_limiter._enforce("k", rules, Response())
    with pytest.raises(HTTPException):
        rate_limiter._enforce("k", rules, Response())


# ---------------------------------------------------------------------------
# Outbound LLM throttle
# ---------------------------------------------------------------------------

def test_token_bucket_wait_time():
    clock = FakeClock()
    b = TokenBucket(60, 60, clock)  # 1 token / second
    b.consume(60)
    assert b.wait_time(10) == pytest.approx(10)
    clock.advance(4)
    assert b.wait_time(10) == pytest.approx(6)


def test_oversized_request_still_runs():
    b = TokenBucket(100, 60, FakeClock())
    assert b.wait_time(10_000) == 0  # capped at capacity, never deadlocks


def _limiter(rpm, tpm):
    clock = FakeClock()
    slept = []

    async def fake_sleep(s):
        slept.append(s)
        clock.advance(s)

    return LLMRateLimiter(rpm, tpm, clock=clock, sleep=fake_sleep), clock, slept


def test_llm_limiter_queues_instead_of_failing_on_rpm():
    lim, _, slept = _limiter(rpm=2, tpm=1_000_000)

    async def go():
        for _ in range(3):
            await lim.acquire(10)

    asyncio.run(go())
    # 3rd request waits for one request-token to refill: 60s / 2 = 30s
    assert sum(slept) == pytest.approx(30)


def test_llm_limiter_respects_tpm():
    lim, _, slept = _limiter(rpm=1000, tpm=6000)

    async def go():
        await lim.acquire(5000)
        await lim.acquire(3000)  # needs 2000 more tokens -> 20s at 100 tok/s

    asyncio.run(go())
    assert sum(slept) == pytest.approx(20)


def test_record_actual_refunds_overestimate():
    lim, _, slept = _limiter(rpm=1000, tpm=6000)

    async def go():
        await lim.acquire(5000)
        lim.record_actual(5000, 1000)  # really used 1000
        await lim.acquire(4000)

    asyncio.run(go())
    assert sum(slept) == 0


def test_penalise_blocks_queued_callers():
    lim, _, slept = _limiter(rpm=1000, tpm=1_000_000)
    lim.penalise(5)

    async def go():
        await lim.acquire(10)

    asyncio.run(go())
    assert sum(slept) >= 5


def test_estimate_tokens_is_reasonable():
    msgs = [{"role": "user", "content": "x" * 4000}]
    assert 1000 <= estimate_tokens(msgs, 0) <= 1100
