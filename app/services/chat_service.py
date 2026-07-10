from app.schemas.chat import ChatResponse
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieval_service
from app.services.conversation_service import conversation_service
from fastapi import HTTPException
from app.services.chat_session_service import (chat_session_service)

class ChatService:

    async def process_message(
        self,
        session_id: int,
        user_id: int,
        message: str
    ) -> ChatResponse:

        session = chat_session_service.get_session(
            session_id=session_id,
            user_id=user_id
            )
        if session.title == "New Chat":

            title = message.strip()

            if len(title) > 40:
                title = title[:37] + "..."

            chat_session_service.update_title(
                session_id=session.id,
                title=title
            )

        if session is None:

            raise HTTPException(
                status_code=403,
                detail="You do not have access to this chat session."
            )
        
        history = (
            conversation_service
            .get_recent_conversations(session_id=session_id)
        )
        print("HISTORY:")
        print(history)

        context = retrieval_service.retrieve(
            message
        )

        answer = await llm_service.generate_response(
            context=context,
            history=history,
            question=message
        )

        conversation_service.save_conversation(
            session_id=session_id,
            user_id=user_id,
            message=message,
            answer=answer
        )

        return ChatResponse(
            answer=answer
        )


chat_service = ChatService()