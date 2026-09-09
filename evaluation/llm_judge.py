"""
LLM-as-judge for open-ended questions that don't have a single exact
expected answer (e.g. "my laptop is slow, what should I do?").

Deliberately scores against hand-written `reference_notes` pulled from the
source PDFs — NOT against the retrieved context — so a bad retrieval can't
grade itself as correct just because the answer matches what was retrieved.
"""

import json

import httpx

from app.core.config import settings

JUDGE_SYSTEM_PROMPT = """You are a strict evaluator for a customer support AI.
You will be given a customer question, a reference list of facts/steps that
a correct answer should reflect, and the AI's actual answer.

Score the AI's answer from 1 to 5 using this rubric:
5 - Fully correct: covers all key facts/steps from the reference, no errors.
4 - Mostly correct: covers the key facts/steps with a minor omission, no errors.
3 - Partially correct: covers some but misses important facts/steps, or is vague.
2 - Mostly incorrect: largely wrong, irrelevant, or contradicts the reference.
1 - Incorrect: wrong, irrelevant, or contains fabricated (hallucinated) information.

Respond with ONLY a JSON object and nothing else:
{"score": <integer 1-5>, "reasoning": "<one sentence>"}
"""


async def judge_answer(
    question: str,
    reference_notes: str,
    generated_answer: str,
) -> dict:
    """
    Calls the same LLM backend the app uses (Groq, per settings.MODEL_NAME)
    to score a generated answer. Returns {"score": int | None, "reasoning": str}.
    score is None if the call failed or the response couldn't be parsed —
    callers should treat None as "unscored", not as a failing score.
    """

    user_prompt = (
        f"Question: {question}\n\n"
        f"Reference facts/steps a correct answer should reflect:\n"
        f"{reference_notes}\n\n"
        f"AI's actual answer:\n{generated_answer}"
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.MODEL_NAME,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            # Some models wrap JSON in a markdown fence despite instructions.
            if raw.startswith("```"):
                raw = raw.strip("`")
                if "\n" in raw:
                    first_line, rest = raw.split("\n", 1)
                    raw = rest if first_line.strip().lower() in ("", "json") else raw

            parsed = json.loads(raw)

            return {
                "score": int(parsed["score"]),
                "reasoning": parsed.get("reasoning", ""),
            }

    except Exception as e:
        return {
            "score": None,
            "reasoning": f"Judge call failed or returned unparseable output: {e!r}",
        }
