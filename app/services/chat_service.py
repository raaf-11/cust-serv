from app.schemas.chat import ChatResponse

from app.services.llm_service import (
    llm_service
)

from app.services.retrieval_service import (
    retrieval_service
)


class ChatService:

    async def process_message(
        self,
        message: str
    ) -> ChatResponse:

        context = retrieval_service.retrieve(
            message
        )

        answer = await llm_service.generate_response(
            context=context,
            question=message
        )

        return ChatResponse(
            answer=answer
        )


chat_service = ChatService()