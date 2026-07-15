from app.db.database import SessionLocal
from app.models.conversation import Conversation


class ConversationService:

    def save_conversation(
        self,
        session_id: int,
        sender: str,
        content: str
    ):

        db = SessionLocal()

        conversation = Conversation(
            session_id=session_id,
            sender=sender,
            content=content
        )

        db.add(conversation)
        db.commit()
        db.close()

    def get_recent_conversations(
        self,
        session_id: int,
        limit: int = 10
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
                f"{conversation.sender}: "
                f"{conversation.content}\n"
            )

        return history


conversation_service = ConversationService()