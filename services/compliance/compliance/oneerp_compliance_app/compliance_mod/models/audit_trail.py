"""감사 추적(AuditTrail) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class AuditAction(StrEnum):
    """감사 행위 유형."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUBMIT = "submit"
    CANCEL = "cancel"
    APPROVE = "approve"


class AuditTrail(BaseDocument):
    """감��� 추적 문서 — 시스템 자동 생성, 사용자 직접 생성 불가."""

    entity_type: str = ""
    entity_id: str = ""
    action: AuditAction = AuditAction.CREATE
    user: str = ""
    timestamp: datetime | None = None
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditTrailCreate(BaseModel):
    """감사 추적 생성 스키마 (내부용)."""

    entity_type: str
    entity_id: str
    action: AuditAction
    user: str
    timestamp: datetime
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditTrailUpdate(BaseModel):
    """감사 추적 수정 스키마 — 감사 추적은 수정 불가, 형식적 선언."""

    ip_address: str | None = None
