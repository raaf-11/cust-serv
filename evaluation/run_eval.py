"""
Run the full evaluation suite against the live pipeline and produce a
detailed report.

Usage (from the project root, with Qdrant/Elasticsearch/Postgres running
and the knowledge base already ingested):

    python -m evaluation.run_eval

Writes a timestamped .json (raw results + report) and .md (human-readable)
report to results/, and prints a summary to the console.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from evaluation.metrics import aggregate_report
from evaluation.runner import EvalRunner

DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _fmt_pct(value) -> str:
    return f"{value * 100:.1f}%" if value is not None else "n/a"


def _fmt_score(value) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def print_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total questions:            {report['total_items']}")
    print(f"Retrieval hit rate:         {_fmt_pct(report['retrieval_hit_rate'])}")
    print(
        f"Factual answer accuracy:   "
        f"{_fmt_pct(report['factual_accuracy'])} "
        f"({report['factual_count']} questions)"
    )
    print(
        f"Avg open-ended judge score: "
        f"{_fmt_score(report['avg_judge_score'])} / 5 "
        f"({report['open_ended_count']} questions)"
    )
    print(f"Avg confidence score:      {report['avg_confidence']:.3f}")
    print(f"Escalation rate:           {_fmt_pct(report['escalation_rate'])}")
    print(f"False escalation rate:     {_fmt_pct(report['false_escalation_rate'])}"
          f"  (correct answers that got escalated anyway)")
    print(f"Missed escalation rate:    {_fmt_pct(report['missed_escalation_rate'])}"
          f"  (wrong answers shown to the customer, unescalated)")
    print(
        f"Avg retrieval / generation time: "
        f"{report['avg_retrieval_time_s']:.2f}s / "
        f"{report['avg_generation_time_s']:.2f}s"
    )
    print("\nPer category:")
    for category, stats in report["per_category"].items():
        rate = stats["correct"] / stats["total"] if stats["total"] else 0.0
        print(f"  {category:<20} {stats['correct']}/{stats['total']} ({rate * 100:.0f}%)")
    print("=" * 60)


def write_markdown_report(path: Path, report: dict, results: list[dict]) -> None:
    lines = []
    lines.append(f"# Evaluation Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total questions:** {report['total_items']}")
    lines.append(f"- **Retrieval hit rate:** {_fmt_pct(report['retrieval_hit_rate'])}")
    lines.append(
        f"- **Factual answer accuracy:** {_fmt_pct(report['factual_accuracy'])} "
        f"({report['factual_count']} questions)"
    )
    lines.append(
        f"- **Avg open-ended judge score:** {_fmt_score(report['avg_judge_score'])} / 5 "
        f"({report['open_ended_count']} questions)"
    )
    lines.append(f"- **Avg confidence score:** {report['avg_confidence']:.3f}")
    lines.append(f"- **Escalation rate:** {_fmt_pct(report['escalation_rate'])}")
    lines.append(
        f"- **False escalation rate:** {_fmt_pct(report['false_escalation_rate'])} "
        f"— correct answers escalated unnecessarily"
    )
    lines.append(
        f"- **Missed escalation rate:** {_fmt_pct(report['missed_escalation_rate'])} "
        f"— wrong answers shown to the customer without escalation"
    )
    lines.append(
        f"- **Avg retrieval / generation time:** "
        f"{report['avg_retrieval_time_s']:.2f}s / {report['avg_generation_time_s']:.2f}s"
    )
    lines.append("")
    lines.append("## Per category")
    lines.append("")
    lines.append("| Category | Correct | Total | Rate |")
    lines.append("|---|---|---|---|")
    for category, stats in report["per_category"].items():
        rate = stats["correct"] / stats["total"] if stats["total"] else 0.0
        lines.append(f"| {category} | {stats['correct']} | {stats['total']} | {rate * 100:.0f}% |")
    lines.append("")
    lines.append("## Per-question detail")
    lines.append("")
    lines.append("| ID | Category | Question | Result | Confidence | Escalate | Retrieval hit |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        status = "PASS" if r["is_correct"] else "FAIL"
        hit = "—" if r["retrieval_hit"] is None else ("yes" if r["retrieval_hit"] else "no")
        lines.append(
            f"| {r['id']} | {r['category']} | {r['question']} | {status} | "
            f"{r['confidence']:.2f} | {r['would_escalate']} | {hit} |"
        )
    lines.append("")
    lines.append("## Failures (full detail)")
    lines.append("")
    failures = [r for r in results if not r["is_correct"]]
    if not failures:
        lines.append("None — every question passed.")
    for r in failures:
        lines.append(f"### {r['id']} — {r['question']}")
        lines.append(f"- Category: {r['category']}")
        lines.append(f"- Expected source: {r.get('expected_source')}")
        lines.append(f"- Retrieved sources: {r['retrieved_sources']}")
        if r["question_type"] == "factual":
            lines.append(f"- Expected answer contains: (see golden_dataset.json)")
        else:
            lines.append(f"- Judge score: {r['judge_score']}")
            lines.append(f"- Judge reasoning: {r['judge_reasoning']}")
        lines.append(f"- Generated answer: {r['generated_answer']}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    dataset = load_dataset()
    print(f"Loaded {len(dataset)} golden questions from {DATASET_PATH.name}\n")

    runner = EvalRunner(dataset)

    def on_item_done(index, total, result):
        status = "PASS" if result["is_correct"] else "FAIL"
        print(
            f"[{index}/{total}] {result['category']:<18} "
            f"{status:<4} conf={result['confidence']:.2f} "
            f"escalate={result['would_escalate']!s:<5} "
            f"{result['question'][:55]}"
        )

    results = await runner.run_all(on_item_done=on_item_done)
    report = aggregate_report(results)
    print_summary(report)

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = RESULTS_DIR / f"eval_report_{timestamp}.json"
    md_path = RESULTS_DIR / f"eval_report_{timestamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"report": report, "results": results}, f, indent=2)

    write_markdown_report(md_path, report, results)

    print(f"\nSaved detailed report to:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
