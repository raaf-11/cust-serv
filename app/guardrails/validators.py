from app.guardrails.exceptions import GuardrailViolation, GuardrailViolationType

MAX_INPUT_LENGTH = 2000  # characters — tune to your token budget


def validate_not_empty(text: str) -> None:
    if not text or not text.strip():
        raise GuardrailViolation(
            violation_type=GuardrailViolationType.EMPTY_INPUT,
            user_message="Please enter a message before sending.",
            detail="Input was empty or whitespace-only.",
        )


def validate_max_length(text: str, max_length: int = MAX_INPUT_LENGTH) -> None:
    if len(text) > max_length:
        raise GuardrailViolation(
            violation_type=GuardrailViolationType.MAX_LENGTH_EXCEEDED,
            user_message=f"Your message is too long. Please limit it to {max_length} characters.",
            detail=f"Input length {len(text)} exceeded max {max_length}.",
        )