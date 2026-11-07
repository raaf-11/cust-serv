from enum import Enum


class GuardrailViolationType(str, Enum):
    EMPTY_INPUT = "EMPTY_INPUT"
    MAX_LENGTH_EXCEEDED = "MAX_LENGTH_EXCEEDED"
    UNGROUNDED_RESPONSE = "UNGROUNDED_RESPONSE"


class GuardrailViolation(Exception):
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
