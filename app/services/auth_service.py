from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.core.security import security_service
from app.schemas.auth import (LoginRequest,TokenResponse)

class AuthService:

    def register(
        self,
        request: RegisterRequest
    ):

        db = SessionLocal()

        existing_user = (
            db.query(User)
            .filter(
                User.email == request.email
            )
            .first()
        )

        if existing_user:

            db.close()

            raise ValueError(
                "Email already registered."
            )

        hashed_password = security_service.hash_password(
            request.password
        )

        user = User(
            name=request.name,
            email=request.email,
            hashed_password=hashed_password
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        db.close()

        return user


    def login(
    self,
    request: LoginRequest
) -> TokenResponse:

        db = SessionLocal()

        user = (
        db.query(User)
        .filter(
            User.email == request.email
        )
        .first()
        )

        if not user:

            db.close()

            raise ValueError(
            "Invalid email or password."
            )

        valid = security_service.verify_password(
        request.password,
        user.hashed_password
        )

        if not valid:

            db.close()

            raise ValueError(
            "Invalid email or password."
            )

        token = security_service.create_access_token(
        user.id
        )

        db.close()

        return TokenResponse(
        access_token=token
        )


auth_service = AuthService()