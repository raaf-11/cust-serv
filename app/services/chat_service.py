from pathlib import Path

from app.schemas.chat import ChatResponse
from app.services.llm_service import llm_service
from app.core.config import settings


class ChatService:

    def _load_system_prompt(self) -> str:

        prompt_path = Path("app/prompts/support_prompt.txt")

        return prompt_path.read_text(
            encoding="utf-8"
        )

    async def process_message(
        self,
        message: str
    ) -> ChatResponse:

        system_prompt = self._load_system_prompt()

        answer = await llm_service.generate_response(
            system_prompt=system_prompt,
            user_message=message,
            temperature=settings.TEMPERATURE
        )

        return ChatResponse(
            answer=answer
        )


chat_service = ChatService()