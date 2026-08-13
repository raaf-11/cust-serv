from fastapi import HTTPException

from app.guardrails.guardrail_service import GuardrailService
from app.guardrails.exceptions import GuardrailViolation
from app.schemas.chat import ChatResponse
from app.services.chat_session_service import chat_session_service
from app.services.conversation_service import conversation_service
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieval_service
from app.services.ticket_service import ticket_service
from app.services.confidence_service import confidence_service

class ChatService:

    def __init__(self):
        self.guardrail_service = GuardrailService()

    async def process_message(
        self,
        session_id: int,
        user_id: int,
        message: str
    ) -> ChatResponse:

        # -----------------------------
        # Input Guardrails
        # -----------------------------
        try:
            message = self.guardrail_service.validate_and_sanitize_input(message)
        except GuardrailViolation as e:
            return ChatResponse(
                answer=e.user_message
            )

        session = chat_session_service.get_session(
            session_id=session_id,
            user_id=user_id
        )

        if session is None:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this chat session."
            )

        if session.title == "New Chat":
            title = message.strip()

            if len(title) > 40:
                title = title[:37] + "..."

            chat_session_service.update_title(
                session_id=session.id,
                title=title
            )

        history = conversation_service.get_recent_conversations(
            session_id=session_id
        )

        print("HISTORY:")
        print(history)

        conversation_service.save_conversation(
            session_id=session_id,
            sender="USER",
            content=message
        )

        active_ticket = ticket_service.get_active_ticket(
            session_id=session_id
        )

        if active_ticket:
            return ChatResponse(
                answer="Your conversation has been assigned to a support agent. Please wait for their response."
            )

        retrieval_result = retrieval_service.retrieve(message)

        context = retrieval_result["context"]
        documents = retrieval_result["documents"]
        confidence_score = confidence_service.calculate_confidence(documents)
        should_escalate = confidence_service.should_escalate(confidence_score)

        print("CONFIDENCE SCORE:", confidence_score)
        print("SHOULD ESCALATE:", should_escalate)
        
        answer = await llm_service.generate_response(
            context=context,
            history=history,
            question=message
        )

        # -----------------------------
        # Output Guardrails
        # -----------------------------
        try:
            self.guardrail_service.validate_output(
                response=answer,
                context=context
            )

        except GuardrailViolation as e:
            answer = e.user_message

        conversation_service.save_conversation(
            session_id=session_id,
            sender="AI",
            content=answer
        )

        return ChatResponse(
            answer=answer
        )


chat_service = ChatService()