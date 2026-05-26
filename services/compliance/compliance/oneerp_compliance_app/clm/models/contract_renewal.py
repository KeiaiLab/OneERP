"""계약 갱신(ContractRenewal) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ContractRenewalCreate(BaseModel):
    """계약 갱신 생성 요청 스키마."""

    contract_id: str
    renewal_date: date | None = None
    new_end_date: date | None = None
    new_value: Decimal = Decimal(0)
    price_change_pct: Decimal = Decimal(0)
    approved_by: str = ""
    status: str = "draft"


class ContractRenewalUpdate(BaseModel):
    """계약 갱신 수정 요청 스키마."""

    contract_id: str | None = None
    renewal_date: date | None = None
    new_end_date: date | None = None
    new_value: Decimal | None = None
    price_change_pct: Decimal | None = None
    approved_by: str | None = None
    status: str | None = None


class ContractRenewal(BaseDocument):
    """계약 갱신 문서."""

    contract_id: str = ""
    renewal_date: date | None = None
    new_end_date: date | None = None
    new_value: Decimal = Decimal(0)
    price_change_pct: Decimal = Decimal(0)
    approved_by: str = ""
    status: str = "draft"
