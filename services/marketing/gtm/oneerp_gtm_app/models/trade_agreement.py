"""무역협정 모델 — FTA/RCEP 등 무역협정과 원산지 규정을 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class TradeAgreementCreate(BaseModel):
    """무역협정 생성 요청 스키마."""

    agreement_name: str
    agreement_code: str
    agreement_type: str = "FTA"  # FTA/RCEP/EPA/CEPA
    country_codes: list[str] = []
    effective_date: date | None = None
    expiry_date: date | None = None
    description: str = ""


class TradeAgreementUpdate(BaseModel):
    """무역협정 수정 요청 스키마."""

    agreement_name: str | None = None
    agreement_type: str | None = None
    country_codes: list[str] | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    description: str | None = None
    is_active: bool | None = None


class TradeAgreement(BaseDocument):
    """무역협정 문서 — FTA/RCEP 등의 협정 정보를 저장한다."""

    agreement_name: str = ""
    agreement_code: str = ""
    agreement_type: str = "FTA"
    country_codes: list[str] = []
    effective_date: date | None = None
    expiry_date: date | None = None
    description: str = ""
    is_active: bool = True
