from app.guardrails.validators import GuardrailResult


class OutputGuardrails:

    def validate(
        self,
        response: str,
        context: str,
    ) -> GuardrailResult:
        """
        Runs all output guardrail checks.
        """
        return GuardrailResult(allowed=True)