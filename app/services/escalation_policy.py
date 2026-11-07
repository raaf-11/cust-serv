import os
import re
from enum import Enum


class Action(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    ESCALATE = "ESCALATE"
    SMALL_TALK = "SMALL_TALK"


def _configured_max_unresolved() -> int:
    try:
        from app.core.config import settings

        return settings.MAX_UNRESOLVED_TURNS
    except Exception:
        return int(os.getenv("MAX_UNRESOLVED_TURNS", "2"))


MAX_UNRESOLVED_TURNS = _configured_max_unresolved()

NO_INFO_PHRASE = "I don't have enough information"

CLARIFY_MESSAGE = (
    "I couldn't find a clear answer to that in our help articles. "
    "Could you rephrase it or add a bit more detail - for example which "
    "product it's about and what exactly is happening? If I still can't "
    "help, I'll pass you to our support team."
)

ESCALATE_AFTER_RETRY_MESSAGE = (
    "Sorry, I still couldn't find a reliable answer for this. I've created "
    "a support ticket and passed your conversation to our support team. "
    "They'll reply here soon."
)

ESCALATE_ON_REQUEST_MESSAGE = (
    "Sure - I've created a support ticket and passed your conversation to "
    "our support team. They'll reply here soon."
)

ALREADY_ESCALATED_MESSAGE = (
    "Your request is already with our support team (ticket #{ticket_id}). "
    "They'll reply here soon. Meanwhile, feel free to ask me anything else."
)


_HUMAN_PATTERNS = [
    r"\b(talk|speak|chat|connect|transfer)\w*\s+(me\s+)?(to|with)\s+"
    r"(a|an|the|some|your)?\s*(real\s+|live\s+)?"
    r"(human|person|agent|someone|somebody|representative|executive|"
    r"support\s+team|support\s+agent|staff|manager)\b",
    r"\b(real|live|human)\s+(person|agent|human|support)\b",
    r"\b(raise|create|open|file|log)\s+(a\s+|an\s+)?(support\s+)?"
    r"(ticket|complaint)\b",
    r"\bescalate\b",
]
_HUMAN_RE = re.compile("|".join(_HUMAN_PATTERNS), re.IGNORECASE)


def wants_human(message: str) -> bool:
    return bool(_HUMAN_RE.search(message or ""))


_GREETING_RE = re.compile(
    r"^(hi+|hello+|hey+|hiya|yo|good\s+(morning|afternoon|evening)|"
    r"greetings)(\s+(there|team|bot|claude|everyone))?$",
    re.IGNORECASE,
)
_THANKS_RE = re.compile(
    r"^(thanks|thank\s+you|thx|ty|cheers)(\s+(so|very)\s+much)?"
    r"(\s+(a\s+lot|again))?$|^(ok|okay|cool|great|got\s+it|perfect|nice)"
    r"(\s+(thanks|thank\s+you))?$",
    re.IGNORECASE,
)
_BYE_RE = re.compile(
    r"^(bye|goodbye|see\s+you|see\s+ya|cya)(\s+later)?$", re.IGNORECASE
)


def _clean(message: str) -> str:
    text = re.sub(r"[^\w\s']", " ", message or "")
    return re.sub(r"\s+", " ", text).strip()


def small_talk_reply(message: str) -> str | None:
    text = _clean(message)

    if _GREETING_RE.match(text):
        return "Hi! How can I help you today?"

    if _THANKS_RE.match(text):
        return "You're welcome! Is there anything else I can help you with?"

    if _BYE_RE.match(text):
        return "Goodbye! Feel free to come back any time."

    return None


def is_unresolved_reply(ai_message: str | None) -> bool:
    if not ai_message:
        return False

    return (
        ai_message.startswith(CLARIFY_MESSAGE[:40])
        or NO_INFO_PHRASE.lower() in ai_message.lower()
    )


def count_trailing_unresolved(recent_ai_messages: list[str]) -> int:
    count = 0

    for message in reversed(recent_ai_messages):
        if not is_unresolved_reply(message):
            break
        count += 1

    return count


def decide(
    message: str,
    low_confidence: bool,
    previous_unresolved: int,
) -> Action:
    if wants_human(message):
        return Action.ESCALATE

    if small_talk_reply(message) is not None:
        return Action.SMALL_TALK

    if low_confidence:
        if previous_unresolved + 1 >= MAX_UNRESOLVED_TURNS:
            return Action.ESCALATE
        return Action.CLARIFY

    return Action.ANSWER


def should_escalate_after_answer(
    answer: str,
    previous_unresolved: int,
) -> bool:
    return (
        is_unresolved_reply(answer) and previous_unresolved + 1 >= MAX_UNRESOLVED_TURNS
    )
