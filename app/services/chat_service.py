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
from app.services import escalation_policy
from app.services.escalation_policy import Action


class ChatService:

    def __init__(self):
        self.guardrail_service = GuardrailService()

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

        # Bot replies so far, used to count "couldn't help" turns in a row.
        previous_ai_messages = conversation_service.get_recent_ai_messages(
            session_id=session_id
        )
        previous_unresolved = escalation_policy.count_trailing_unresolved(
            previous_ai_messages
        )

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

        # -------------------------------------------------------------
        # 1. Cheap checks first: explicit hand-off request / small talk.
        #    These never need retrieval.
        # -------------------------------------------------------------

        if escalation_policy.wants_human(message):
            return self._escalate(
                user_id=user_id,
                session_id=session_id,
                message=message,
                answer=escalation_policy.ESCALATE_ON_REQUEST_MESSAGE,
                subject="Customer requested a support agent"
            )

        small_talk = escalation_policy.small_talk_reply(message)

        if small_talk is not None:
            return self._reply(session_id, small_talk)

        # -------------------------------------------------------------
        # 2. Retrieval + confidence
        # -------------------------------------------------------------

        retrieval_result = retrieval_service.retrieve(message)

        context = retrieval_result["context"]
        documents = retrieval_result["documents"]

        confidence_score = confidence_service.calculate_confidence(documents)
        low_confidence = confidence_service.should_escalate(confidence_score)

        action = escalation_policy.decide(
            message=message,
            low_confidence=low_confidence,
            previous_unresolved=previous_unresolved
        )

        print(
            f"CONFIDENCE={confidence_score} LOW={low_confidence} "
            f"PREVIOUS_UNRESOLVED={previous_unresolved} ACTION={action.value}"
        )

        if action == Action.CLARIFY:
            return self._reply(session_id, escalation_policy.CLARIFY_MESSAGE)

        if action == Action.ESCALATE:
            return self._escalate(
                user_id=user_id,
                session_id=session_id,
                message=message,
                answer=escalation_policy.ESCALATE_AFTER_RETRY_MESSAGE,
                subject="AI Support Escalation"
            )

        # -------------------------------------------------------------
        # 3. Answer with the LLM
        # -------------------------------------------------------------

        answer = await llm_service.generate_response(
            context=context,
            history=history,
            question=message
        )

        # Retrieval looked OK but the model still couldn't answer, and the
        # previous turn was also a miss -> hand off instead of looping.
        if escalation_policy.should_escalate_after_answer(
            answer, previous_unresolved
        ):
            return self._escalate(
                user_id=user_id,
                session_id=session_id,
                message=message,
                answer=escalation_policy.ESCALATE_AFTER_RETRY_MESSAGE,
                subject="AI Support Escalation"
            )

        return self._reply(session_id, answer)

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _reply(self, session_id: int, answer: str) -> ChatResponse:

        conversation_service.save_conversation(
            session_id=session_id,
            sender="AI",
            content=answer
        )

        return ChatResponse(answer=answer)

    def _escalate(
        self,
        user_id: int,
        session_id: int,
        message: str,
        answer: str,
        subject: str
    ) -> ChatResponse:

        # Never open a second ticket for the same conversation.
        existing = ticket_service.get_unresolved_ticket(
            session_id=session_id
        )

        if existing:
            return self._reply(
                session_id,
                escalation_policy.ALREADY_ESCALATED_MESSAGE.format(
                    ticket_id=existing.id
                )
            )

        ticket_service.create_ticket(
            user_id=user_id,
            session_id=session_id,
            subject=subject,
            description=message
        )

        return self._reply(session_id, answer)


chat_service = ChatService()
