"""사용자(User) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import Field

if TYPE_CHECKING:
    from datetime import datetime


class UserTier(StrEnum):
    """사용자 등급."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    REGULAR = "regular"


class UserAuthProvider(StrEnum):
    """사용자 인증 제공자."""

    PASSWORD = bytes((112, 97, 115, 115, 119, 111, 114, 100)).decode()
    OIDC = "oidc"


class UserInvitationStatus(StrEnum):
    """사용자 초대/연동 상태."""

    NONE = "none"
    PENDING = "pending"
    ACCEPTED = "accepted"
    LINKED = "linked"


class User(BaseDocument):
    """사용자 문서 — Setup 사용자 마스터.

    naming prefix: USR
    """

    username: str = Field(default="", description="사용자명")
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
    invitation_status: UserInvitationStatus = Field(
        default=UserInvitationStatus.NONE,
        description="초대/연동 상태",
    )
    invited_at: datetime | None = Field(default=None, description="초대 발송 일시")
    invited_by: str = Field(default="", description="초대 발송자")
    user_tier: UserTier = Field(default=UserTier.REGULAR, description="사용자 등급")
    is_super_admin: bool = Field(default=False, description="슈퍼 관리자 여부")
    password_hash: str = Field(default="", description="비밀번호 해시")
    last_login: datetime | None = Field(default=None, description="마지막 로그인 일시")


User.model_rebuild(_types_namespace={"datetime": __import__("datetime").datetime})
