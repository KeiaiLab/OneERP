"""문서 감사 로그(DocumentAuditLog) 모델 — 문서 접근/변경 행위 기록.

BR-DOC-014: 모든 문서 접근/변경 시 감사 로그 필수 기록.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class AuditAction(StrEnum):
    """감사 로그 행위 유형."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DOWNLOAD = "download"
    SHARE = "share"
    SIGN = "sign"
    CHECKOUT = "checkout"
    CHECKIN = "checkin"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    DISPOSE = "dispose"
    RESTORE_VERSION = "restore_version"
    ACCESS_DENIED = "access_denied"


class DocumentAuditLogCreate(BaseModel):
    """감사 로그 생성 요청 스키마."""

    document_id: str = Field(description="문서 ID")
    action: AuditAction = Field(description="행위 유형")
    actor: str = Field(description="행위자")
    actor_ip: str = Field(default="", description="접속 IP")
    actor_user_agent: str = Field(default="", description="브라우저/앱 정보")
    details: dict[str, object] = Field(default_factory=dict, description="상세 정보")
    previous_state: dict[str, object] = Field(default_factory=dict)
    new_state: dict[str, object] = Field(default_factory=dict)


class DocumentAuditLogUpdate(BaseModel):
    """감사 로그 수정 스키마 (일반적으로 사용하지 않음 — 로그는 불변)."""

    details: dict[str, object] | None = None


class DocumentAuditLog(BaseDocument):
    """문서 감사 로그 엔티티.

    문서에 대한 모든 접근/변경 행위를 기록한다.
    감사 추적 및 보안 모니터링에 사용한다.
    """

    document_id: str = ""
    action: AuditAction = AuditAction.READ
    actor: str = ""
    actor_ip: str = ""
    actor_user_agent: str = ""
    details: dict[str, object] = Field(default_factory=dict)
    previous_state: dict[str, object] = Field(default_factory=dict)
    new_state: dict[str, object] = Field(default_factory=dict)
    timestamp: datetime | None = None
