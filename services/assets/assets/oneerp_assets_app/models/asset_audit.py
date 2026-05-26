"""자산실사(AssetAudit) 문서 모델 — Assets 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetAuditCreate(BaseModel):
    """자산실사 생성 요청 스키마."""

    audit_date: date | None = None
    auditor: str = ""
    asset: str = ""
    location: str = ""
    condition: str = "good"
    remarks: str = ""


class AssetAuditUpdate(BaseModel):
    """자산실사 수정 요청 스키마."""

    audit_date: date | None = None
    auditor: str | None = None
    asset: str | None = None
    location: str | None = None
    condition: str | None = None
    remarks: str | None = None


class AssetAudit(BaseDocument):
    """자산실사 문서 — Assets 자산실사 트랜잭션.

    naming prefix: AAUD
    """

    audit_date: date | None = None
    auditor: str = ""
    asset: str = ""
    location: str = ""
    condition: str = "good"
    remarks: str = ""
