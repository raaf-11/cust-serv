from app.schemas.chat import ChatResponse


class ChatService:
    async def process_message(self, message: str) -> ChatResponse:
        return ChatResponse(
            answer=f"You said: {message}"
        )


chat_service = ChatService()