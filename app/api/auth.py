from fastapi import APIRouter, HTTPException
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)
from app.services.auth_service import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
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
    response_model=TokenResponse
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