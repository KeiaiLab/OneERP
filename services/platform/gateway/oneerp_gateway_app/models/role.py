"""역할(Role) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """역할 생성 요청 스키마."""

    role_name: str = Field(description="역할명")
    description: str = Field(default="", description="설명")
    is_custom: bool = Field(default=False, description="커스텀 역할 여부")
    is_system: bool = Field(default=False, description="시스템 내장 역할 여부 (삭제 불가)")
    scope: str = Field(default="tenant", description="범위 ('platform' 또는 'tenant')")


class RoleUpdate(BaseModel):
    """역할 수정 요청 스키마."""

    role_name: str | None = Field(default=None, description="역할명")
    description: str | None = Field(default=None, description="설명")
    is_custom: bool | None = Field(default=None, description="커스텀 역할 여부")
    is_system: bool | None = Field(default=None, description="시스템 내장 역할 여부 (삭제 불가)")
    scope: str | None = Field(default=None, description="범위 ('platform' 또는 'tenant')")


class Role(BaseDocument):
    """역할 문서 — Setup 역할 마스터.

    naming prefix: ROL
    """

    role_name: str = Field(default="", description="역할명")
    description: str = Field(default="", description="설명")
    is_custom: bool = Field(default=False, description="커스텀 역할 여부")
    is_system: bool = Field(default=False, description="시스템 내장 역할 여부 (삭제 불가)")
    scope: str = Field(default="tenant", description="범위 ('platform' 또는 'tenant')")
