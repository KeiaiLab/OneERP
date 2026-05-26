"""감사 추적(AuditTrail) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AuditTrailCreate(BaseModel):
    """감사 추적 생성 요청 스키마."""

    entity_type: str
    entity_id: str = ""
    action: str = ""
    actor: str = ""
    changes: str = ""


class AuditTrailUpdate(BaseModel):
    """감사 추적 수정 요청 스키마."""

    entity_type: str | None = None
    entity_id: str | None = None
    action: str | None = None
    actor: str | None = None
    changes: str | None = None


class AuditTrail(BaseDocument):
    """감사 추적 문서."""

    entity_type: str = ""
    entity_id: str = ""
    action: str = ""
    actor: str = ""
    changes: str = ""
