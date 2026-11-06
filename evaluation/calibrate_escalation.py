"""
Escalation calibration — retrieval only, no LLM calls, runs in ~30s.

Runs three groups of questions through the real retrieval pipeline and
prints the confidence each one gets, with the OLD and NEW formulas:

  answerable   golden_dataset.json questions        -> should NOT escalate
  typos        same questions with a typo injected   -> should NOT escalate
  off-topic    things the KB can't answer            -> should be LOW

Usage (from the project root, with Qdrant + Elasticsearch running):

    python -m evaluation.calibrate_escalation

If any answerable/typo question is flagged LOW, or an off-topic one is not,
the script suggests a CONFIDENCE_THRESHOLD to put in your .env.
"""

import json
import re
from pathlib import Path

from app.services.confidence_service import confidence_service
from app.services.retrieval_service import retrieval_service

DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

HAND_WRITTEN_TYPOS = [
    "How long is the standard warranty for laptp?",
    "my laptp is runing slowly what should i do",
    "how do i reset my pasword",
    "how long does a upi refnd take",
    "how many delivry attempts are made",
    "warrenty for mobile phnes",
]

OFF_TOPIC = [
    "What's the weather like in Chennai today?",
    "Who won the cricket match yesterday?",
    "Can you book me a flight to Delhi?",
    "Give me a recipe for chicken biryani",
    "What is the capital of Australia?",
    "Write me a poem about the sea",
]


def legacy_confidence(documents: list[dict]) -> float:
    """The original formula, for side-by-side comparison."""

    if not documents:
        return 0.0

    rerank = [d["rerank_score"] for d in documents if d.get("rerank_score") is not None]
    if not rerank:
        return 0.0

    gap = rerank[0] - rerank[1] if len(rerank) > 1 else 0.0
    gap_score = min(gap / 2.0, 1.0)

    top_source = documents[0].get("document_name")
    agreement = sum(d.get("document_name") == top_source for d in documents) / len(documents)

    vectors = [d["vector_score"] for d in documents if d.get("vector_score") is not None]
    vector = max(0.0, min(max(vectors), 1.0)) if vectors else 0.0

    return round(0.5 * vector + 0.3 * agreement + 0.2 * gap_score, 4)


def inject_typo(question: str) -> str:
    """Drop one interior letter from the longest word (deterministic)."""

    words = re.findall(r"[A-Za-z]+", question)
    longest = max(words, key=len)

    if len(longest) < 5:
        return question

    middle = len(longest) // 2
    typo = longest[:middle] + longest[middle + 1:]
    return question.replace(longest, typo, 1)


def score(question: str) -> dict:
    result = retrieval_service.retrieve(question)
    docs = result["documents"]

    return {
        "question": question,
        "search_query": result.get("search_query", question),
        "old": legacy_confidence(docs),
        "new": confidence_service.calculate_confidence(docs),
        "top_rerank": round(docs[0]["rerank_score"], 2) if docs else None,
        "top_source": docs[0].get("document_name") if docs else None,
    }


def main() -> None:
    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    groups = {
        "answerable": [item["question"] for item in dataset],
        "typos": [inject_typo(item["question"]) for item in dataset] + HAND_WRITTEN_TYPOS,
        "off-topic": OFF_TOPIC,
    }

    threshold = confidence_service.threshold
    rows = {name: [score(q) for q in qs] for name, qs in groups.items()}

    print()
    print(f"NEW threshold = {threshold}   (old formula used 0.40)")
    print("=" * 110)

    for name, results in rows.items():
        print(f"\n{name.upper()}")
        print(f"{'old':>6} {'new':>6} {'rerank':>7}  {'flag':<5} question  [-> corrected query]")

        for r in results:
            low = r["new"] < threshold
            expected_low = name == "off-topic"
            flag = "LOW" if low else "ok"
            mark = "" if low == expected_low else "  <-- WRONG"
            corrected = (
                f"  [-> {r['search_query']}]"
                if r["search_query"] != r["question"] else ""
            )
            print(
                f"{r['old']:>6.2f} {r['new']:>6.2f} {r['top_rerank']:>7} "
                f" {flag:<5} {r['question'][:60]}{corrected}{mark}"
            )

    good = [r["new"] for r in rows["answerable"] + rows["typos"]]
    bad = [r["new"] for r in rows["off-topic"]]

    print("\n" + "=" * 110)
    print(f"Lowest answerable/typo confidence : {min(good):.3f}")
    print(f"Highest off-topic confidence      : {max(bad):.3f}")

    if max(bad) < min(good):
        suggestion = round((max(bad) + min(good)) / 2, 2)
        print(f"Clean separation. Any threshold between them works; "
              f"midpoint = {suggestion}")
        if not (max(bad) < threshold < min(good)):
            print(f"-> Set CONFIDENCE_THRESHOLD={suggestion} in your .env")
        else:
            print("-> Current threshold is fine.")
    else:
        print("Groups overlap — look at the WRONG rows above. Off-topic "
              "questions with high scores usually mean the KB genuinely "
              "has a loosely related chunk; that's OK because the LLM will "
              "say it doesn't know, and the next miss escalates.")


if __name__ == "__main__":
    main()
