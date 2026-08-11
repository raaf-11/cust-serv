from app.guardrails import validators, sanitizer, output_guardrails
from app.guardrails.exceptions import GuardrailViolation  # re-exported for convenience


class GuardrailService:
    """
    Single entry point ChatService talks to. ChatService should never
    import directly from validators.py, sanitizer.py, or
    output_guardrails.py — this facade hides the internal structure,
    the same role RetrievalService plays in front of HybridRetriever.
    """

    def validate_and_sanitize_input(self, text: str) -> str:
        """
        Runs input-side checks (fail fast, cheapest first), then
        returns a sanitized version of the text safe to pass into
        retrieval, the prompt, and storage.
        """
        validators.validate_not_empty(text)
        validators.validate_max_length(text)
        return sanitizer.sanitize_text(text)

    def validate_output(self, response: str, context: str) -> None:
        """
        Verifies the LLM's response is grounded in the retrieved
        context. Raises GuardrailViolation if not — caller is
        responsible for substituting e.user_message before storing
        or returning the response.
        """
        output_guardrails.validate_grounding(response, context)