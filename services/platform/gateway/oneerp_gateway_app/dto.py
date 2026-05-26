"""gateway identity 요청/응답 DTO 집약."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .models.user import UserAuthProvider, UserTier


class LoginRequest(BaseModel):
    """로그인 요청 스키마."""

    username: str = Field(description="사용자명")
    password: str = Field(description="비밀번호")


class TokenResponse(BaseModel):
    """토큰 응답 스키마."""

    access_token: str = Field(description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 유형")
    expires_in: int = Field(description="만료 시간(초)")


class UserCreate(BaseModel):
    """사용자 생성 요청 스키마."""

    username: str = Field(description="사용자명")
    email: str = Field(default="", description="이메일")
    full_name: str = Field(default="", description="성명")
    is_active: bool = Field(default=True, description="활성 여부")
    role: str = Field(default="", description="역할 (하위 호환)")
    roles: list[str] = Field(default_factory=list, description="역할 목록 (다중 역할)")
    company_id: str = Field(default="", description="소속 회사 ID")
    department_name: str = Field(default="", description="소속 부서명")
    auth_provider: UserAuthProvider = Field(
        default=UserAuthProvider.PASSWORD,
        description="인증 제공자",
    )
    oidc_subject: str = Field(default="", description="OIDC subject")
    user_tier: UserTier = Field(default=UserTier.REGULAR, description="사용자 등급")
    is_super_admin: bool = Field(default=False, description="슈퍼 관리자 여부")
    password: str = Field(default="", description="비밀번호")


class UserUpdate(BaseModel):
    """사용자 수정 요청 스키마."""

    username: str | None = Field(default=None, description="사용자명")
    email: str | None = Field(default=None, description="이메일")
    full_name: str | None = Field(default=None, description="성명")
    is_active: bool | None = Field(default=None, description="활성 여부")
    role: str | None = Field(default=None, description="역할 (하위 호환)")
    roles: list[str] | None = Field(default=None, description="역할 목록 (다중 역할)")
    company_id: str | None = Field(default=None, description="소속 회사 ID")
    department_name: str | None = Field(default=None, description="소속 부서명")
    auth_provider: UserAuthProvider | None = Field(default=None, description="인증 제공자")
    oidc_subject: str | None = Field(default=None, description="OIDC subject")
    user_tier: UserTier | None = Field(default=None, description="사용자 등급")
    is_super_admin: bool | None = Field(default=None, description="슈퍼 관리자 여부")
    password: str | None = Field(default=None, description="비밀번호")
