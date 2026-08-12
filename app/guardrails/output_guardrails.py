import re
from typing import List

import numpy as np

from app.guardrails.exceptions import GuardrailViolation, GuardrailViolationType
from app.services.embedding_service import embedding_service


# -----------------------------
# Numeric grounding
# -----------------------------
# Catches fabricated/injected numeric claims (dates, %, currency) by
# checking whether the exact number in the response actually appears
# in the retrieved context. Cheap, deterministic, no model call needed.

_NUMBER_ANCHOR_RE = re.compile(
    r"\b\d+\s*(days?|months?|years?|hours?|%|percent|₹|\$|rs\.?)\b",
    re.IGNORECASE,
)


def _extract_anchors(text: str) -> list[str]:
    return [m.group(0).lower() for m in _NUMBER_ANCHOR_RE.finditer(text)]


def validate_grounding(response: str, context: str) -> None:
    """
    Verifies numeric claims in the response (e.g. "90 days", "5%")
    are traceable to the retrieved context. Testing proved the LLM
    will state an injected or invented figure as fact when told to
    by text that merely looks authoritative — this check doesn't
    trust the model's compliance with prompt instructions, it
    verifies the output mechanically after the fact.
    """
    anchors = _extract_anchors(response)
    context_lower = context.lower()

    for anchor in anchors:
        number_match = re.search(r"\d+", anchor)
        if not number_match:
            continue
        number_part = number_match.group(0)

        if number_part not in context_lower:
            raise GuardrailViolation(
                violation_type=GuardrailViolationType.UNGROUNDED_RESPONSE,
                user_message=(
                    "I don't have confirmed information on that — let me "
                    "connect you with a team member who can verify."
                ),
                detail=(
                    f"Unsupported numeric anchor '{anchor}'. "
                    f"Context did not contain '{number_part}'."
                ),
            )


# -----------------------------------
# Semantic grounding
# -----------------------------------
# Catches non-numeric fabricated claims (e.g. "we ship internationally
# with no customs fees") that the numeric check can't see, since there's
# no digit to anchor on. Uses embedding_service — the same service
# VectorRetriever already uses for retrieval — so no new dependency or
# duplicate model load. Cosine similarity between each response sentence
# and the retrieved context stands in for "is this claim traceable to
# what we actually retrieved."

_MIN_SENTENCE_LEN = 15  # skip short filler like "Sure!" or "Let me know."
SIMILARITY_THRESHOLD = 0.45  # starting value — needs calibration, see note below


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _split_sentences(text: str) -> List[str]:
    # Naive splitter — good enough for support-bot-length responses.
    # Avoids pulling in a full NLP tokenizer for marginal accuracy gain.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) >= _MIN_SENTENCE_LEN]


def validate_semantic_grounding(response: str, context: str) -> None:
    """
    Soft-fails deliberately: semantic similarity is fuzzier than exact
    numeric matching, so false positives are more likely. The fallback
    routes to human handoff rather than a hard refusal, so a wrongly
    flagged correct answer costs the customer a slight delay, not a
    dead end.
    """
    if not context.strip():
        return  # nothing retrieved — not this check's job to handle

    sentences = _split_sentences(response)
    if not sentences:
        return

    context_vector = embedding_service.embed(context)

    for sentence in sentences:
        if not sentence.strip():
            continue  # defensive — embed() raises on empty/whitespace text

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