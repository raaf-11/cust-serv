import json

from app.core.config import settings
from app.services.llm_service import post_chat_completion

JUDGE_MODEL_NAME = settings.JUDGE_MODEL_NAME or settings.MODEL_NAME

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
    user_prompt = (
        f"Question: {question}\n\n"
        f"Reference facts/steps a correct answer should reflect:\n"
        f"{reference_notes}\n\n"
        f"AI's actual answer:\n{generated_answer}"
    )

    payload = {
        "model": JUDGE_MODEL_NAME,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    if "gpt-oss" in JUDGE_MODEL_NAME.lower():
        payload["reasoning_effort"] = "low"

    try:
        data = await post_chat_completion(payload)
        raw = data["choices"][0]["message"]["content"].strip()

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
