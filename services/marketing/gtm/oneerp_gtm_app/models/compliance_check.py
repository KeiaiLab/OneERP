"""수출통제 준수점검 모델 — 수출통제 규정 준수 여부를 점검한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class ComplianceCheckCreate(BaseModel):
    """준수점검 생성 요청 스키마."""

    check_type: str = "denied_party"  # denied_party/embargo/dual_use/sanction
    entity_name: str = ""
    entity_country: str = ""
    item_code: str = ""
    hs_code: str = ""
    destination_country: str = ""
    reference_document: str = ""
    reference_id: str = ""


class ComplianceCheckUpdate(BaseModel):
    """준수점검 수정 요청 스키마."""

    result: str | None = None
    risk_level: str | None = None
    remarks: str | None = None


class ComplianceCheck(BaseDocument):
    """준수점검 문서 — 수출통제 규정 준수 검사 결과를 저장한다."""

    check_type: str = "denied_party"
    entity_name: str = ""
    entity_country: str = ""
    item_code: str = ""
    hs_code: str = ""
    destination_country: str = ""
    reference_document: str = ""
    reference_id: str = ""
    result: str = "pending"  # pending/pass/fail/warning
    risk_level: str = "low"  # low/medium/high/critical
    checked_at: datetime | None = None
    matched_lists: list[str] = []
    remarks: str = ""
