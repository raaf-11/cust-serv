from enum import Enum


class GuardrailViolationType(str, Enum):
    """
    Central list of every guardrail failure mode this project currently
    checks for. Kept as a string Enum so violation types are type-checked
    and safe to log/store without risk of typos creating silent new
    categories.
    """

    EMPTY_INPUT = "EMPTY_INPUT"
    MAX_LENGTH_EXCEEDED = "MAX_LENGTH_EXCEEDED"
    UNGROUNDED_RESPONSE = "UNGROUNDED_RESPONSE"


class GuardrailViolation(Exception):
    """
    Raised whenever an input or output guardrail check fails.

    - user_message: safe, generic text shown to the customer. Never
      reveals *why* detection triggered.
    - detail: internal-only diagnostic text, for logs only.
    - violation_type: lets calling code (ChatService, logging, future
      analytics) branch/aggregate on failure category without parsing
      strings.
    """

    def __init__(
        self,
        violation_type: GuardrailViolationType,
        user_message: str,
        detail: str = "",
    ):
        self.violation_type = violation_type
        self.user_message = user_message
        self.detail = detail
        super().__init__(detail or user_message)

    def __repr__(self) -> str:
        return (
            f"GuardrailViolation(type={self.violation_type.value}, "
            f"detail={self.detail!r})"
        )