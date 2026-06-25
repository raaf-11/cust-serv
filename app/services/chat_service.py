from app.schemas.chat import ChatResponse
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieval_service
from app.services.conversation_service import conversation_service


class ChatService:

    async def process_message(
        self,
        session_id: int,
        message: str
    ) -> ChatResponse:

        context = retrieval_service.retrieve(
            message
        )
        history = (
        conversation_service
        .get_recent_conversations(
            session_id=session_id
            )
        )
        print("HISTORY:")
        print(history)

        answer = await llm_service.generate_response(
            context=context,
            history=history,
            question=message
        )
        conversation_service.save_conversation(
            session_id=session_id,
            user_id=1,
            message=message,
            answer=answer
        )

        return ChatResponse(
            answer=answer
        )


chat_service = ChatService()