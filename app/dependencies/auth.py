from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import security_service

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
) -> User:

    token = credentials.credentials

    user_id = security_service.verify_access_token(
        token
    )

    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid token."
        )

    db = SessionLocal()

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    db.close()

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found."
        )

    return user

def require_employee(
    current_user=Depends(get_current_user),
):
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access required",
        )

    return current_user