"""계약(Contract) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ContractCreate(BaseModel):
    """계약 생성 요청 스키마."""

    contract_name: str
    contract_type: str = ""
    template_id: str | None = None
    party_type: str = ""
    party_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    currency: str = "KRW"
    auto_renew: bool = False
    renewal_notice_days: int = 0
    signed_date: date | None = None
    signed_by: str = ""
    electronic_stamp_tax: Decimal = Decimal(0)
    status: str = "draft"


class ContractUpdate(BaseModel):
    """계약 수정 요청 스키마."""

    contract_name: str | None = None
    contract_type: str | None = None
    template_id: str | None = None
    party_type: str | None = None
    party_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal | None = None
    currency: str | None = None
    auto_renew: bool | None = None
    renewal_notice_days: int | None = None
    signed_date: date | None = None
    signed_by: str | None = None
    electronic_stamp_tax: Decimal | None = None
    status: str | None = None


class Contract(BaseDocument):
    """계약 문서."""

    contract_name: str = ""
    contract_type: str = ""
    template_id: str | None = None
    party_type: str = ""
    party_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    currency: str = "KRW"
    auto_renew: bool = False
    renewal_notice_days: int = 0
    signed_date: date | None = None
    signed_by: str = ""
    electronic_stamp_tax: Decimal = Decimal(0)
    status: str = "draft"
