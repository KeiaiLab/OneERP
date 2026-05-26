"""인증(Auth) 라우트 — JWT 로그인/갱신/로그아웃."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from ..dto import LoginRequest, TokenResponse
from ..services.auth_service import login as login_user
from ..services.auth_service import logout as logout_user
from ..services.auth_service import refresh as refresh_user

router = APIRouter(prefix="/api/v1/auth", tags=["인증"])


@router.post("/login")
def login(body: LoginRequest, response: Response, request: Request) -> TokenResponse:
    """사용자 로그인 — JWT 발급."""
    result = login_user(
        username=body.username, password=body.password, request=request, response=response
    )
    return TokenResponse(**result)


@router.post("/refresh")
def refresh_token(request: Request, response: Response) -> TokenResponse:
    """리프레시 토큰으로 새 액세스 토큰을 발급한다."""
    return TokenResponse(**refresh_user(request=request, response=response))


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    """로그아웃 — 쿠키 삭제."""
    return logout_user(response=response)
