"""계약 갱신(ContractRenewal) 문서 모델.

gateway에서 CRM으로 이관됨.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class ContractRenewalStatus(StrEnum):
    """계약 갱신 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    RENEWED = "renewed"


class ContractRenewalCreate(BaseModel):
    """계약 갱신 생성 요청 스키마."""

    contract_id: str
    renewal_date: date | None = None
    new_end_date: date | None = None
    revised_value: Decimal = Decimal(0)
    reason: str = ""


class ContractRenewalUpdate(BaseModel):
    """계약 갱신 수정 요청 스키마."""

    contract_id: str | None = None
    renewal_date: date | None = None
    new_end_date: date | None = None
    revised_value: Decimal | None = None
    reason: str | None = None


class ContractRenewal(BaseDocument):
    """계약 갱신 문서."""

    status: ContractRenewalStatus = Field(
        default=ContractRenewalStatus.DRAFT,
        description="계약 갱신 상태",
    )
    contract_id: str = ""
    renewal_date: date | None = None
    new_end_date: date | None = None
    revised_value: Decimal = Decimal(0)
    reason: str = ""
