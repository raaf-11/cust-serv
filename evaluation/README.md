# Evaluation

Automated evaluation for the RAG pipeline: retrieval quality, answer
correctness, and confidence/escalation calibration — run either as a
detailed report or as a pass/fail regression suite.

## Why this exists

`Test Questions.txt` was a manual QA checklist. This package turns it into
something repeatable: a **golden dataset** of question/expected-answer
pairs (expanded from 6 to 24 questions across all 8 knowledge-base
documents), and a harness that runs each question through the *actual*
retrieval + confidence + generation pipeline and scores the result.

It deliberately calls `retrieval_service`, `confidence_service`, and
`llm_service` directly rather than going through `ChatService` or the HTTP
API — that keeps the eval fast, avoids needing a JWT/user/session, and
(more importantly) lets us always generate an answer even for questions
the app *would* escalate, so we can measure whether escalation is actually
catching the right things (see "Confidence calibration" below).

## What's measured

| Layer | Metric | What it tells you |
|---|---|---|
| Retrieval | `retrieval_hit_rate` | Did the correct source PDF get retrieved at all? |
| Answer quality (factual) | `factual_accuracy` | Does the generated answer contain the expected fact? (heuristic substring/token match — see `metrics.contains_answer`) |
| Answer quality (open-ended) | `avg_judge_score` | An LLM judge (1–5) scores answers like "my laptop is slow" against hand-written reference notes pulled from the source PDF — not against the retrieved context, so a bad retrieval can't grade itself as correct. |
| Confidence calibration | `escalation_rate`, `false_escalation_rate`, `missed_escalation_rate` | Is the 0.60 threshold in `confidence_service.py` well-tuned? See below. |
| Performance | `avg_retrieval_time_s`, `avg_generation_time_s` | Rough latency budget per stage. |

### Confidence calibration, explained

For every question we record both the confidence score and whether the
*actual generated answer* was correct — including for questions that
would have been escalated in production. That gives two numbers that a
single "accuracy" figure hides:

- **False escalation rate** — of the questions flagged for escalation,
  what fraction would have been answered correctly anyway? High = the
  threshold is too conservative, and customers get bounced to a human
  needlessly.
- **Missed escalation rate** — of the questions the system got *wrong*,
  what fraction were never escalated? This is the dangerous one: a wrong
  answer shown to a customer with no human safety net. Watch this number
  most closely.

## Prerequisites

The eval runs against the live pipeline, so before running it:

1. Qdrant, Elasticsearch, and Postgres are up (however you normally run
   them for local dev).
2. The knowledge base PDFs in `data/` have been ingested (via the
   ingestion endpoint/service) so retrieval has something to find.
3. `.env` has a valid API key — the LLM judge makes its own API calls, in
   addition to the ones the pipeline itself makes, so a full run costs
   ~2x the API usage of just chatting through the 24 questions.
4. `pip install -r evaluation/requirements-eval.txt` (kept separate from
   the project's `requirements.txt`, which is UTF-16 encoded and best left
   untouched by hand).

## Running it

**Detailed report** (console summary + saved `.json`/`.md` in `results/`):

```bash
python -m evaluation.run_eval
```

**Pass/fail regression suite:**

```bash
pytest tests/test_eval.py -v
```

Tests are *skipped*, not failed, if Qdrant/Elasticsearch aren't reachable
— see `tests/conftest.py`. Thresholds live at the top of `test_eval.py`;
they're deliberately conservative starting points, not targets to hit
exactly. If a threshold fails, check the markdown report for the specific
failing questions before assuming the number itself needs adjusting.

## Extending the dataset

Add entries to `golden_dataset.json`. Each item needs:

- `id`, `category`, `question`, `question_type` (`"factual"` or `"open_ended"`)
- `expected_source` — the PDF filename in `data/`, used for retrieval hit-rate
- factual items: `expected_answer` — a short fact the answer should contain
- open-ended items: `reference_notes` — a short, hand-written summary of
  what a correct answer should cover (pulled from the source PDF, written
  independently of what retrieval currently returns)

## Known limitations

- `contains_answer()` is a heuristic (normalized substring + token match).
  It handles common paraphrasing (dashes, "X to Y" vs "X-Y") but isn't
  bulletproof — spot-check the `generated_answer` field in the JSON report
  for anything borderline rather than trusting the PASS/FAIL label blindly.
- The LLM judge uses the same model/provider as the app itself
  (`MODEL_NAME` in `.env`), so a systematic blind spot in that model could
  affect both the answer *and* its own grading. Worth occasionally
  spot-checking judge scores by eye, or swapping in a different judge model.
- 24 questions is enough to catch regressions, not enough to be a
  statistically rigorous benchmark — treat swings of 1-2 questions as
  noise, not signal.
