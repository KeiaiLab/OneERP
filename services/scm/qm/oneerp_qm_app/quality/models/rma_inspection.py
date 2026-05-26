"""반품 검사(RmaInspection) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class RmaInspectionCreate(BaseModel):
    """반품 검사 생성 요청 스키마."""

    rma_id: str
    inspection_date: date | None = None
    inspector: str = ""
    condition: str = ""
    findings: str = ""
    disposition: str = ""


class RmaInspectionUpdate(BaseModel):
    """반품 검사 수정 요청 스키마."""

    rma_id: str | None = None
    inspection_date: date | None = None
    inspector: str | None = None
    condition: str | None = None
    findings: str | None = None
    disposition: str | None = None


class RmaInspection(BaseDocument):
    """반품 검사 문서."""

    rma_id: str = ""
    inspection_date: date | None = None
    inspector: str = ""
    condition: str = ""
    findings: str = ""
    disposition: str = ""
