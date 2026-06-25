from app.db.database import SessionLocal
from app.models.conversation import Conversation



class ConversationService:

    def save_conversation(
        self,
        session_id: int,
        user_id: int,
        message: str,
        answer: str
    ):

        db = SessionLocal()

        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            message=message,
            answer=answer
        )

        db.add(conversation)

        db.commit()

        db.close()

    def get_recent_conversations(
        self,
        session_id: int,
        limit: int = 5
    ) -> str:

        db = SessionLocal()

        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == session_id
            )
            .order_by(
                Conversation.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        db.close()

        conversations.reverse()

        history = ""

        for conversation in conversations:
            history += (
                f"User: {conversation.message}\n"
                f"Assistant: {conversation.answer}\n\n"
            )

        return history


conversation_service = ConversationService()