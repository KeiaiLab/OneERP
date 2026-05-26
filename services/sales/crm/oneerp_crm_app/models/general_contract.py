"""일반 계약(Contract) 문서 모델.

ServiceContract(서비스 계약)와 구분하기 위해 general_contract로 명명한다.
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


class ContractStatus(StrEnum):
    """계약 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractCreate(BaseModel):
    """계약 생성 요청 스키마."""

    contract_title: str
    counterparty: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    currency: str = "KRW"


class ContractUpdate(BaseModel):
    """계약 수정 요청 스키마."""

    contract_title: str | None = None
    counterparty: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal | None = None
    currency: str | None = None


class Contract(BaseDocument):
    """계약 문서."""

    status: ContractStatus = Field(
        default=ContractStatus.DRAFT,
        description="계약 상태",
    )
    contract_title: str = ""
    counterparty: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    currency: str = "KRW"
