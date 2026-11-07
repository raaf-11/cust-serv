import re
from typing import List

import numpy as np

from app.guardrails.exceptions import GuardrailViolation, GuardrailViolationType

_NUM = r"\d+(?:[.,]\d+)?"
_TIME_UNIT = r"(minute|hour|day|week|month|year)s?\b"
_QUALIFIER = r"(?:\s+(?:business|working|calendar|full|consecutive))?"
_CURRENCY = r"(?:₹|\$|\brs\.?)"

_TIME_RE = re.compile(rf"(?<![\d.,])({_NUM}){_QUALIFIER}\s*{_TIME_UNIT}", re.IGNORECASE)
_PERCENT_RE = re.compile(rf"(?<![\d.,])({_NUM})\s*(?:%|percent\b)", re.IGNORECASE)
_MONEY_RE = re.compile(rf"{_CURRENCY}\s*({_NUM})(?![\d])", re.IGNORECASE)

_NOT_DIGIT_AFTER = r"(?![\d]|[.,]\d)"


def _claims(text: str) -> list[tuple[str, str, re.Pattern]]:
    claims = []

    for m in _TIME_RE.finditer(text):
        num, unit = re.escape(m.group(1)), m.group(2).lower()
        pattern = re.compile(
            rf"(?<![\d.,]){num}{_NOT_DIGIT_AFTER}"
            rf"(?:\s*(?:-|–|to)\s*{_NUM})?(?:\s+[a-z]+){{0,2}}\s*{unit}s?\b",
            re.IGNORECASE,
        )
        claims.append((m.group(0), m.group(1), pattern))

    for m in _PERCENT_RE.finditer(text):
        num = re.escape(m.group(1))
        pattern = re.compile(rf"(?<![\d.,]){num}\s*(?:%|percent\b)", re.IGNORECASE)
        claims.append((m.group(0), m.group(1), pattern))

    for m in _MONEY_RE.finditer(text):
        num = re.escape(m.group(1))
        pattern = re.compile(rf"{_CURRENCY}\s*{num}{_NOT_DIGIT_AFTER}", re.IGNORECASE)
        claims.append((m.group(0), m.group(1), pattern))

    return claims


def validate_grounding(response: str, context: str) -> None:
    for anchor, number, pattern in _claims(response):
        if not pattern.search(context):
            raise GuardrailViolation(
                violation_type=GuardrailViolationType.UNGROUNDED_RESPONSE,
                user_message=(
                    "I don't have confirmed information on that — let me "
                    "connect you with a team member who can verify."
                ),
                detail=(
                    f"Unsupported figure '{anchor}': context has no "
                    f"'{number}' with the same unit."
                ),
            )


_MIN_SENTENCE_LEN = 15
SIMILARITY_THRESHOLD = 0.45


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) >= _MIN_SENTENCE_LEN]


def validate_semantic_grounding(response: str, context: str) -> None:
    if not context.strip():
        return

    sentences = _split_sentences(response)
    if not sentences:
        return

    from app.services.embedding_service import embedding_service

    context_vector = embedding_service.embed(context)

    for sentence in sentences:
        if not sentence.strip():
            continue

        sentence_vector = embedding_service.embed(sentence)
        score = _cosine_similarity(sentence_vector, context_vector)

        if score < SIMILARITY_THRESHOLD:
            raise GuardrailViolation(
                violation_type=GuardrailViolationType.UNGROUNDED_RESPONSE,
                user_message=(
                    "I don't have confirmed information on that — let me "
                    "connect you with a team member who can verify."
                ),
                detail=(
                    f"Sentence below similarity threshold "
                    f"({score:.2f} < {SIMILARITY_THRESHOLD}): '{sentence}'"
                ),
            )
