from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class SecurityService:

    def hash_password(
        self,
        password: str
    ) -> str:

        return pwd_context.hash(
            password
        )

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:

        return pwd_context.verify(
            plain_password,
            hashed_password
        )

    def create_access_token(
        self,
        user_id: int
    ) -> str:

        expire = datetime.now(
            timezone.utc
        ) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": str(user_id),
            "exp": expire
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def verify_access_token(
        self,
        token: str
    ) -> int | None:

        try:

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            return int(
                payload["sub"]
            )

        except JWTError:

            return None


security_service = SecurityService()