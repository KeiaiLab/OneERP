"""감사 로그(AuditLog) 문서 모델.

엔티티 정의: L2-spec 1.12
"""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """감사 로그 생성 요청 스키마."""

    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_ip: str | None = None
    changes: dict[str, Any] | None = None


class AuditLogUpdate(BaseModel):
    """감사 로그 수정 요청 스키마 (사용하지 않음)."""


class AuditLog(BaseDocument):
    """감사 로그 문서.

    게시판 모듈의 모든 주요 행위(CRUD, 좋아요, 북마크, 신고)를 기록한다.
    """

    entity_type: str = ""
    entity_id: str = ""
    action: str = ""
    actor_id: str = ""
    actor_ip: str | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
