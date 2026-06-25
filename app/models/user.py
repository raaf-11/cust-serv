from sqlalchemy import Column, Integer, String
from datetime import datetime
from app.db.database import Base
from sqlalchemy import DateTime

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )
    
    hashed_password = Column(
    String,
    nullable=False
            )

    created_at = Column(
    DateTime,
    default=datetime.utcnow
    )