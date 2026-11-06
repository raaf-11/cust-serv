"""
Fast unit tests for the escalation logic. No Qdrant, Elasticsearch or LLM
needed:  pytest tests/test_escalation_policy.py -q
"""

from app.services import escalation_policy as policy
from app.services.escalation_policy import Action
from app.services.confidence_service import ConfidenceService
from app.services.query_normalizer import QueryNormalizer

KB_TEXT = [
    "The standard warranty for laptops is 2 years from the date of purchase.",
    "If your laptop is running slowly, restart it and close background apps.",
    "Password reset links are valid for 15 minutes.",
    "UPI refunds take 3-5 business days. Delivery attempts: 3.",
    "Mobile phones carry a 1 year warranty.",
]


# ---------------------------------------------------------------------------
# Typo correction
# ---------------------------------------------------------------------------

def make_normalizer():
    return QueryNormalizer(text_loader=lambda: KB_TEXT)


def test_laptp_is_corrected():
    n = make_normalizer()
    assert n.normalize("warranty for laptp?") == "warranty for laptop?"


def test_common_typos_are_corrected():
    n = make_normalizer()
    assert n.normalize("pasword reset") == "password reset"
    assert n.normalize("warrenty for phnes") == "warranty for phones"
    assert n.normalize("refnd").startswith("refund")


def test_correct_and_everyday_words_are_untouched():
    n = make_normalizer()
    for q in ["hello there", "thanks", "My laptop is running slowly",
              "what is the weather today", "I want to talk to a human"]:
        assert n.normalize(q) == q


def test_normalizer_fails_open_when_kb_unreachable():
    def broken():
        raise ConnectionError("elasticsearch down")

    n = QueryNormalizer(text_loader=broken)
    assert n.normalize("laptp") == "laptp"


def test_normalizer_is_deterministic():
    n = make_normalizer()
    results = {n.normalize("my laptp is runing slowly") for _ in range(20)}
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def doc(rerank, vector, name="Warranty_Policy.pdf"):
    return {"rerank_score": rerank, "vector_score": vector, "document_name": name}


def test_good_match_is_confident_even_with_mixed_sources_and_no_gap():
    # Old formula punished this (different PDFs, top two chunks tied).
    svc = ConfidenceService(threshold=0.25)
    docs = [
        doc(6.0, 0.55, "Warranty_Policy.pdf"),
        doc(6.0, 0.52, "Laptop_Troubleshooting_Guide.pdf"),
        doc(1.0, 0.40, "Refund_and_Return_Policy.pdf"),
    ]
    score = svc.calculate_confidence(docs)
    assert score > 0.8
    assert not svc.should_escalate(score)


def test_irrelevant_results_are_low():
    svc = ConfidenceService(threshold=0.25)
    docs = [doc(-9.5, 0.12), doc(-10.2, 0.10)]
    assert svc.should_escalate(svc.calculate_confidence(docs))


def test_no_documents_is_low():
    svc = ConfidenceService(threshold=0.25)
    assert svc.should_escalate(svc.calculate_confidence([]))


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

def test_single_low_confidence_message_asks_to_clarify_not_escalate():
    assert policy.decide("blah", low_confidence=True, previous_unresolved=0) == Action.CLARIFY


def test_second_miss_in_a_row_escalates():
    assert policy.decide("blah", low_confidence=True, previous_unresolved=1) == Action.ESCALATE


def test_good_answer_resets_the_streak():
    history = [policy.CLARIFY_MESSAGE, "The laptop warranty is 2 years."]
    assert policy.count_trailing_unresolved(history) == 0

    history = ["The laptop warranty is 2 years.", policy.CLARIFY_MESSAGE]
    assert policy.count_trailing_unresolved(history) == 1


def test_llm_dont_know_counts_as_unresolved():
    history = ["I don't have enough information to answer that."]
    assert policy.count_trailing_unresolved(history) == 1
    assert policy.should_escalate_after_answer(
        "I don't have enough information to answer that.", previous_unresolved=1
    )
    assert not policy.should_escalate_after_answer(
        "I don't have enough information to answer that.", previous_unresolved=0
    )


def test_explicit_human_request_escalates_immediately():
    for msg in ["I want to talk to a human", "can I speak with an agent please",
                "connect me to a real person", "please raise a ticket",
                "escalate this"]:
        assert policy.decide(msg, low_confidence=False, previous_unresolved=0) == Action.ESCALATE, msg


def test_normal_questions_are_not_human_requests():
    for msg in ["My laptop is running slowly", "how long is the warranty",
                "what does the support team do on weekends?",
                "is the agent warranty transferable"]:
        assert not policy.wants_human(msg), msg


def test_small_talk_never_escalates():
    for msg in ["hi", "Hello!", "hey there", "thanks", "thank you so much",
                "ok thanks", "bye"]:
        assert policy.decide(msg, low_confidence=True, previous_unresolved=5) == Action.SMALL_TALK, msg


def test_greeting_plus_question_is_not_small_talk():
    assert policy.small_talk_reply("hi, my laptp is slow") is None


def test_demo_scenario_laptp_does_not_escalate():
    """The embarrassing demo case, end to end through the pure logic."""
    n = make_normalizer()
    query = n.normalize("How long is the standard warranty for laptp?")
    assert "laptop" in query
    # Even if retrieval were weak, the first miss only asks to rephrase.
    assert policy.decide(query, low_confidence=True, previous_unresolved=0) != Action.ESCALATE
