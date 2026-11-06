import asyncio
import logging
import random
import re
from pathlib import Path

import httpx

from app.core.config import settings
from app.services.llm_rate_limiter import estimate_tokens, llm_rate_limiter

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

FALLBACK_RESPONSE = (
    "I'm currently unavailable. Please try again later."
)

# Shown when the provider is still rate limiting us after all retries.
# Kept separate from FALLBACK_RESPONSE so logs/evals can tell "busy" from
# "broken".
RATE_LIMITED_RESPONSE = (
    "We're handling a lot of requests right now. Please try again in a minute."
)

# Status codes worth retrying: rate limited, or a transient provider error.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Hard cap on answer length (also bounds reasoning tokens on gpt-oss).
MAX_COMPLETION_TOKENS = 1024
# Typical answer length, used only for the throttle's token estimate.
EXPECTED_COMPLETION_TOKENS = 350


# Qwen3 is a "thinking" model and may emit <think>...</think> before the
# answer. That reasoning is different on every call, so strip it.
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


class LLMRateLimitedError(Exception):
    """Provider kept returning 429 after every retry."""


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """
    Groq sends `retry-after` (seconds) on 429s. Fall back to the
    x-ratelimit-reset-* headers ("2.5s", "1m3s", "120ms") if it's missing.
    """

    value = response.headers.get("retry-after")
    if value:
        try:
            return float(value)
        except ValueError:
            pass

    for header in ("x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
        value = response.headers.get(header)
        if value:
            parsed = _parse_duration(value)
            if parsed is not None:
                return parsed

    return None


_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m|h)")


def _parse_duration(text: str) -> float | None:
    parts = _DURATION_RE.findall(text)
    if not parts:
        return None
    scale = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
    return sum(float(n) * scale[u] for n, u in parts)


async def post_chat_completion(
    payload: dict,
    max_retries: int | None = None,
    max_retry_wait_s: float | None = None,
) -> dict:
    """
    POST to Groq's chat completions endpoint with:
      * client-side throttling (RPM + TPM token buckets), and
      * retries on 429/5xx that honour Retry-After, else exponential
        backoff with jitter.

    Returns the parsed JSON. Raises LLMRateLimitedError if still rate
    limited after all retries, or the underlying httpx error otherwise.
    Shared by the chat path and the eval's LLM judge so both respect the
    same budget.
    """

    if max_retries is None:
        max_retries = settings.LLM_MAX_RETRIES
    if max_retry_wait_s is None:
        max_retry_wait_s = settings.LLM_MAX_RETRY_WAIT_S

    payload.setdefault("max_tokens", MAX_COMPLETION_TOKENS)

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    estimated = estimate_tokens(payload["messages"], EXPECTED_COMPLETION_TOKENS)

    async with httpx.AsyncClient(timeout=60) as client:

        for attempt in range(max_retries + 1):

            waited = await llm_rate_limiter.acquire(estimated)
            if waited > 0.05:
                logger.info("LLM throttle: waited %.1fs for capacity", waited)

            response = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)

            if response.status_code < 400:
                data = response.json()
                actual = (data.get("usage") or {}).get("total_tokens")
                llm_rate_limiter.record_actual(estimated, actual)
                return data

            if response.status_code not in RETRYABLE_STATUS or attempt == max_retries:
                if response.status_code == 429:
                    raise LLMRateLimitedError(response.text[:300])
                response.raise_for_status()

            hinted = _retry_after_seconds(response)
            backoff = hinted if hinted is not None else (2 ** attempt) + random.uniform(0, 1)

            if backoff > max_retry_wait_s:
                # Waiting that long would make the user stare at a spinner;
                # better to tell them now.
                if response.status_code == 429:
                    raise LLMRateLimitedError(
                        f"retry-after {backoff:.0f}s exceeds max wait {max_retry_wait_s:.0f}s"
                    )
                response.raise_for_status()

            if response.status_code == 429:
                # Make every queued request back off too, not just this one.
                llm_rate_limiter.penalise(backoff)

            logger.warning(
                "LLM API returned %s, retrying in %.1fs (attempt %d/%d)",
                response.status_code, backoff, attempt + 1, max_retries,
            )
            await asyncio.sleep(backoff)

    raise RuntimeError("unreachable")


class LLMService:

    def _load_system_prompt(self) -> str:

        prompt_path = Path(
            "app/prompts/support_prompt.txt"
        )

        return prompt_path.read_text(
            encoding="utf-8"
        )

    async def generate_response(
        self,
        context: str,
        history: str,
        question: str
    ) -> str:

        system_prompt = self._load_system_prompt()

        user_prompt = f"""
Conversation History:

{history}

Context:

{context}

Question:

{question}
"""

        payload = {
            "model": settings.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": settings.TEMPERATURE,
            "seed": settings.LLM_SEED
        }

        # Turn off Qwen3's thinking mode on Groq: faster, and removes the
        # biggest source of answer-to-answer variation.
        if "qwen3" in settings.MODEL_NAME.lower():
            payload["reasoning_effort"] = "none"

        # gpt-oss models "think" before answering, and those hidden tokens
        # count towards Groq's tokens-per-minute limit. Keep it short.
        if "gpt-oss" in settings.MODEL_NAME.lower():
            payload["reasoning_effort"] = "low"

        try:

            data = await post_chat_completion(payload)

            content = data["choices"][0]["message"]["content"] or ""

            return THINK_RE.sub("", content).strip()

        except LLMRateLimitedError as e:
            logger.error(f"LLM still rate limited after retries: {e}")
            return RATE_LIMITED_RESPONSE

        except httpx.TimeoutException as e:
            logger.error(f"LLM request timed out: {e!r}")
            return FALLBACK_RESPONSE

        except httpx.HTTPStatusError as e:
            logger.error(
                "LLM API returned %s: %s",
                e.response.status_code,
                e.response.text[:500]
            )
            return FALLBACK_RESPONSE

        except Exception as e:
            logger.error(f"LLM request failed unexpectedly: {e!r}")
            return FALLBACK_RESPONSE


llm_service = LLMService()
