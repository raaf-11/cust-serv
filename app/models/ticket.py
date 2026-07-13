from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from app.db.database import Base


class Ticket(Base):

    __tablename__ = "tickets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_employee_id = Column(
    Integer,
    ForeignKey("users.id"),
    nullable=True
    )

    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False
    )

    subject = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        default="OPEN",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )