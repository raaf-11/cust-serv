from app.guardrails import validators
from app.guardrails.exceptions import GuardrailViolation
from app.guardrails.output_guardrails import validate_grounding


class GuardrailService:
    def validate_input(self, text: str) -> None:
        validators.validate_not_empty(text)
        validators.validate_max_length(text)

    def validate_output(self, response: str, context: str) -> None:
        validate_grounding(response, context)
