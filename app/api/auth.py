from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)
from app.services.auth_service import auth_service
from app.dependencies.auth import require_employee
from app.core.config import settings
from app.core.rate_limiter import limit_by_ip



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    dependencies=[Depends(limit_by_ip("register", (settings.REGISTER_RATE_PER_HOUR, 3600)))]
)
def register(
    request: RegisterRequest
):

    try:

        auth_service.register(request)

        return {
            "message": "User registered successfully."
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post(
    "/login",
    response_model=TokenResponse,
    # Per-IP limit against password guessing.
    dependencies=[Depends(limit_by_ip("login", (settings.LOGIN_RATE_PER_MINUTE, 60)))]
)
def login(
    request: LoginRequest
):

    try:

        return auth_service.login(
            request
        )

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
