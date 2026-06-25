from app.db.database import engine
from app.db.database import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.chat_session import ChatSession

Base.metadata.create_all(
    bind=engine
)