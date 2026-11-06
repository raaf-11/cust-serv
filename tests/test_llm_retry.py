"""
429 / retry behaviour of llm_service.post_chat_completion, using a fake
HTTP transport (no real API calls):  pytest tests/test_llm_retry.py -q
"""

import asyncio

import httpx
import pytest

from app.services import llm_service
from app.services.llm_rate_limiter import LLMRateLimiter


def _ok():
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": "hi"}}], "usage": {"total_tokens": 50}},
    )


@pytest.fixture
def fake_api(monkeypatch):
    """Replace the network with a scripted list of responses."""
    script: list[httpx.Response] = []
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(request):
        calls["n"] += 1
        return script.pop(0)

    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr(llm_service.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(llm_service.asyncio, "sleep", fake_sleep)
    limiter = LLMRateLimiter(1000, 1_000_000)
    limiter.penalise = lambda seconds: None  # throttle itself is tested in test_rate_limiter.py
    monkeypatch.setattr(llm_service, "llm_rate_limiter", limiter)
    return script, calls, sleeps


def _payload():
    return {"model": "m", "messages": [{"role": "user", "content": "hello"}]}


def test_retries_429_using_retry_after(fake_api):
    script, calls, sleeps = fake_api
    script += [httpx.Response(429, headers={"retry-after": "3"}), _ok()]

    data = asyncio.run(llm_service.post_chat_completion(_payload(), max_retries=3, max_retry_wait_s=20))

    assert data["choices"][0]["message"]["content"] == "hi"
    assert calls["n"] == 2
    assert 3 in sleeps


def test_gives_up_with_rate_limited_error(fake_api):
    script, calls, _ = fake_api
    script += [httpx.Response(429, headers={"retry-after": "1"})] * 3

    with pytest.raises(llm_service.LLMRateLimitedError):
        asyncio.run(llm_service.post_chat_completion(_payload(), max_retries=2, max_retry_wait_s=20))
    assert calls["n"] == 3


def test_does_not_wait_longer_than_cap(fake_api):
    script, calls, sleeps = fake_api
    script += [httpx.Response(429, headers={"retry-after": "120"})]

    with pytest.raises(llm_service.LLMRateLimitedError):
        asyncio.run(llm_service.post_chat_completion(_payload(), max_retries=3, max_retry_wait_s=20))
    assert calls["n"] == 1 and 120 not in sleeps


def test_non_retryable_error_fails_fast(fake_api):
    script, calls, _ = fake_api
    script += [httpx.Response(401, json={"error": "bad key"})]

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(llm_service.post_chat_completion(_payload(), max_retries=3, max_retry_wait_s=20))
    assert calls["n"] == 1


def test_parses_groq_reset_header():
    r = httpx.Response(429, headers={"x-ratelimit-reset-tokens": "1m3.5s"})
    assert llm_service._retry_after_seconds(r) == pytest.approx(63.5)


def test_generate_response_returns_friendly_message_when_rate_limited(fake_api, monkeypatch):
    script, _, _ = fake_api
    script += [httpx.Response(429, headers={"retry-after": "1"})] * 10
    monkeypatch.setattr(llm_service.LLMService, "_load_system_prompt", lambda self: "sys")

    answer = asyncio.run(llm_service.llm_service.generate_response("ctx", "", "q"))
    assert answer == llm_service.RATE_LIMITED_RESPONSE
