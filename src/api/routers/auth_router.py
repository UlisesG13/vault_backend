"""Endpoints de autenticación."""
from typing import Annotated

from fastapi import APIRouter, Depends

from ...domain.usecases.auth import LoginUseCase
from ..dependencies import get_login_usecase
from ..schemas.auth_schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    usecase: Annotated[LoginUseCase, Depends(get_login_usecase)],
) -> TokenResponse:
    token = usecase.execute(body.email, body.password)
    return TokenResponse(access_token=token)
