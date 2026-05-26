"""역할권한(RolePermission) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RolePermissionCreate(BaseModel):
    """역할권한 생성 요청 스키마."""

    role: str = Field(description="역할")
    doctype: str = Field(description="문서 유형")
    module: str = Field(default="", description="모듈 (selling, crm 등)")
    read: bool = Field(default=True, description="읽기 권한")
    write: bool = Field(default=False, description="쓰기 권한")
    create: bool = Field(default=False, description="생성 권한")
    delete: bool = Field(default=False, description="삭제 권한")
    submit: bool = Field(default=False, description="제출 권한")
    cancel: bool = Field(default=False, description="취소 권한")
    export: bool = Field(default=False, description="내보내기 권한")
    report: bool = Field(default=False, description="리포트 권한")


class RolePermissionUpdate(BaseModel):
    """역할권한 수정 요청 스키마."""

    role: str | None = Field(default=None, description="역할")
    doctype: str | None = Field(default=None, description="문서 유형")
    module: str | None = Field(default=None, description="모듈 (selling, crm 등)")
    read: bool | None = Field(default=None, description="읽기 권한")
    write: bool | None = Field(default=None, description="쓰기 권한")
    create: bool | None = Field(default=None, description="생성 권한")
    delete: bool | None = Field(default=None, description="삭제 권한")
    submit: bool | None = Field(default=None, description="제출 권한")
    cancel: bool | None = Field(default=None, description="취소 권한")
    export: bool | None = Field(default=None, description="내보내기 권한")
    report: bool | None = Field(default=None, description="리포트 권한")


class RolePermission(BaseDocument):
    """역할권한 문서 — Setup 역할권한 마스터.

    naming prefix: RPERM
    """

    role: str = Field(default="", description="역할")
    doctype: str = Field(default="", description="문서 유형")
    module: str = Field(default="", description="모듈 (selling, crm 등)")
    read: bool = Field(default=True, description="읽기 권한")
    write: bool = Field(default=False, description="쓰기 권한")
    create: bool = Field(default=False, description="생성 권한")
    delete: bool = Field(default=False, description="삭제 권한")
    submit: bool = Field(default=False, description="제출 권한")
    cancel: bool = Field(default=False, description="취소 권한")
    export: bool = Field(default=False, description="내보내기 권한")
    report: bool = Field(default=False, description="리포트 권한")
