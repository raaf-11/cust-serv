from app.core.config import settings
from app.guardrails.validators import GuardrailResult


class InputGuardrails:

    def validate(self, message: str) -> GuardrailResult:

        if not message or not message.strip():
            return GuardrailResult(
                allowed=False,
                reason="Message cannot be empty.",
                code="EMPTY_INPUT"
            )

        if len(message) > settings.MAX_INPUT_LENGTH:
            return GuardrailResult(
                allowed=False,
                reason=f"Message exceeds {settings.MAX_INPUT_LENGTH} characters.",
                code="INPUT_TOO_LONG"
            )

        return GuardrailResult(
            allowed=True
        )