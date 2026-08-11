import re
from app.guardrails.exceptions import GuardrailViolation, GuardrailViolationType

# Anchors: numbers tied to days/months/years/percentages/currency —
# the kinds of specific claims that should always trace back to
# retrieved context, never to the model's own invention or an
# injected fake instruction.
_NUMBER_ANCHOR_RE = re.compile(
    r"\b\d+\s*(days?|months?|years?|hours?|%|percent|₹|\$|rs\.?)\b",
    re.IGNORECASE,
)


def _extract_anchors(text: str) -> list[str]:
    return [m.group(0).lower() for m in _NUMBER_ANCHOR_RE.finditer(text)]


def validate_grounding(response: str, context: str) -> None:
    """
    Checks that numeric/factual claims in the LLM's response are
    traceable to the retrieved context actually passed into the prompt.

    Why this exists: testing proved the model will state an injected
    or invented policy (e.g. "refunds are available for 90 days") as
    fact when told to by text that merely looks authoritative — even
    with no such figure anywhere in the retrieved chunks. A prompt
    instruction ("only answer from context") is advisory; the model
    can be talked out of following it. This check doesn't trust that
    instruction — it verifies the output mechanically after the fact.
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
                    f"Response contained unsupported factual anchor "
                    f"'{anchor}'. Context did not contain '{number_part}'."
                ),
            )