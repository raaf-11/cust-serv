from app.guardrails.input_guardrails import InputGuardrails
from app.guardrails.output_guardrails import OutputGuardrails
from app.guardrails.validators import GuardrailResult


class GuardrailService:

    def __init__(self):
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()

    def validate_input(self, message: str) -> GuardrailResult:
        return self.input_guardrails.validate(message)

    def validate_output(
        self,
        response: str,
        context: str,
    ) -> GuardrailResult:
        return self.output_guardrails.validate(
            response=response,
            context=context,
        )