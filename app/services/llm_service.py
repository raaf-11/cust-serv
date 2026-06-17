import httpx

from app.core.config import settings

FALLBACK_RESPONSE = (
    "I'm currently unavailable. Please try again later."
)


class LLMService:

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float
    ) -> str:

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": temperature
        }
        try:
            async with httpx.AsyncClient() as client:

                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                response.raise_for_status()

                data = response.json()

                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            return FALLBACK_RESPONSE

        except httpx.HTTPStatusError:
            return FALLBACK_RESPONSE

        except Exception:
            return FALLBACK_RESPONSE



llm_service = LLMService()