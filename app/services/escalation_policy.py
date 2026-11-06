"""
When should the bot hand a conversation to a human?

Old behaviour: any single message with confidence < 0.40 -> ticket.
That escalated greetings, typos and slightly vague questions on the very
first try.

New behaviour (in priority order):

1. The user explicitly asks for a person ("talk to a human", "raise a
   ticket")                                        -> ESCALATE right away
2. Small talk ("hi", "thanks", "bye")              -> friendly reply, no
                                                      retrieval, never escalate
3. Retrieval found nothing useful:
     - first time in a row                         -> CLARIFY (ask the user to
                                                      rephrase / add detail)
     - again right after a CLARIFY / "don't know"  -> ESCALATE
4. Otherwise                                       -> ANSWER with the LLM

So a human gets involved when the user asks for one, or when the bot has
genuinely failed twice in a row - not because of one weak score.

Pure Python, no app imports, so it's unit-testable without any services.
"""

import os
import re
from enum import Enum


class Action(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    ESCALATE = "ESCALATE"
    SMALL_TALK = "SMALL_TALK"


# How many unresolved bot turns in a row before we escalate (default 2:
# one clarification, then hand-off).
def _configured_max_unresolved() -> int:
    try:
        from app.core.config import settings
        return settings.MAX_UNRESOLVED_TURNS
    except Exception:
        return int(os.getenv("MAX_UNRESOLVED_TURNS", "2"))


MAX_UNRESOLVED_TURNS = _configured_max_unresolved()

# Must match the fallback sentence in app/prompts/support_prompt.txt.
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

# ---------------------------------------------------------------------------
# Explicit requests for a human
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Small talk
# ---------------------------------------------------------------------------

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
_BYE_RE = re.compile(r"^(bye|goodbye|see\s+you|see\s+ya|cya)(\s+later)?$",
                     re.IGNORECASE)


def _clean(message: str) -> str:
    text = re.sub(r"[^\w\s']", " ", message or "")
    return re.sub(r"\s+", " ", text).strip()


def small_talk_reply(message: str) -> str | None:
    """Returns a canned reply for pure small talk, else None."""

    text = _clean(message)

    if _GREETING_RE.match(text):
        return "Hi! How can I help you today?"

    if _THANKS_RE.match(text):
        return "You're welcome! Is there anything else I can help you with?"

    if _BYE_RE.match(text):
        return "Goodbye! Feel free to come back any time."

    return None


# ---------------------------------------------------------------------------
# Unresolved-turn tracking
# ---------------------------------------------------------------------------

def is_unresolved_reply(ai_message: str | None) -> bool:
    """Was this bot reply a 'couldn't help' reply?"""

    if not ai_message:
        return False

    return (
        ai_message.startswith(CLARIFY_MESSAGE[:40])
        or NO_INFO_PHRASE.lower() in ai_message.lower()
    )


def count_trailing_unresolved(recent_ai_messages: list[str]) -> int:
    """
    recent_ai_messages: bot replies, oldest first.
    Returns how many of the most recent ones in a row were unresolved.
    """

    count = 0

    for message in reversed(recent_ai_messages):
        if not is_unresolved_reply(message):
            break
        count += 1

    return count


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

def decide(
    message: str,
    low_confidence: bool,
    previous_unresolved: int,
) -> Action:
    """
    message:             the user's message
    low_confidence:      ConfidenceService.should_escalate(score)
    previous_unresolved: count_trailing_unresolved(previous bot replies)
    """

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
    """
    The retrieval looked fine but the LLM still said it doesn't know.
    Treat that as an unresolved turn too.
    """

    return (
        is_unresolved_reply(answer)
        and previous_unresolved + 1 >= MAX_UNRESOLVED_TURNS
    )
