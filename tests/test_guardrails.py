import pytest

from app.guardrails.exceptions import GuardrailViolation, GuardrailViolationType
from app.guardrails.guardrail_service import GuardrailService
from app.guardrails.validators import MAX_INPUT_LENGTH

guardrails = GuardrailService()

CONTEXT = (
    "UPI refunds take 3-5 business days. "
    "The standard warranty for laptops is 2 years. "
    "Password reset links are valid for 15 minutes."
)


def test_normal_message_passes():
    guardrails.validate_input("How long is the laptop warranty?")


def test_message_at_limit_passes():
    guardrails.validate_input("a" * MAX_INPUT_LENGTH)


def test_too_long_message_is_rejected():
    with pytest.raises(GuardrailViolation) as exc:
        guardrails.validate_input("a" * (MAX_INPUT_LENGTH + 1))
    assert exc.value.violation_type == GuardrailViolationType.MAX_LENGTH_EXCEEDED


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_message_is_rejected(text):
    with pytest.raises(GuardrailViolation) as exc:
        guardrails.validate_input(text)
    assert exc.value.violation_type == GuardrailViolationType.EMPTY_INPUT


def test_grounded_figure_passes():
    guardrails.validate_output("The laptop warranty is 2 years.", CONTEXT)


def test_answer_without_figures_passes():
    guardrails.validate_output(
        "Restart your laptop and close background apps.", CONTEXT
    )


def test_fallback_answer_passes():
    guardrails.validate_output(
        "I don't have enough information to answer that.", CONTEXT
    )


def test_numbered_steps_are_not_treated_as_claims():
    guardrails.validate_output(
        "1. Restart the laptop. 2. Close background apps. 3. Check for updates.",
        CONTEXT,
    )


@pytest.mark.parametrize(
    "answer",
    [
        "UPI refunds take 3-5 business days.",
        "UPI refunds take 3–5 business days.",
        "It can take up to 5 business days.",
        "Reset links expire after 15 minutes.",
        "Refunds take between 3 and 5 days.",
    ],
)
def test_ranges_and_qualifiers_pass(answer):
    guardrails.validate_output(answer, CONTEXT)


def test_word_ending_in_rs_is_not_currency():
    guardrails.validate_output(
        "Within 48 hours 5-7 business days.",
        "Refunds start within 48 hours and take 5-7 business days.",
    )


def test_currency_must_be_grounded():
    ctx = "A restocking fee of ₹500 applies."
    guardrails.validate_output("There is a ₹500 restocking fee.", ctx)
    with pytest.raises(GuardrailViolation):
        guardrails.validate_output("There is a ₹50 restocking fee.", ctx)


@pytest.mark.parametrize(
    "answer",
    [
        "UPI refunds take 10 days.",
        "Password reset links are valid for 5 minutes.",
        "The laptop warranty is 5 years.",
        "You get a 20% discount on returns.",
    ],
)
def test_invented_figure_is_flagged(answer):
    with pytest.raises(GuardrailViolation) as exc:
        guardrails.validate_output(answer, CONTEXT)
    assert exc.value.violation_type == GuardrailViolationType.UNGROUNDED_RESPONSE
    assert "team member" in exc.value.user_message


def test_figure_from_chat_history_passes():
    combined = CONTEXT + "\nUSER: I ordered it 12 days ago"
    guardrails.validate_output("Since you ordered 12 days ago, ...", combined)
