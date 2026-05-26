"""서비스 계약(ServiceContract) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ServiceContractCreate(BaseModel):
    """서비스 계약 생성 요청 스키마."""

    customer_id: str
    contract_type: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    is_active: bool = True


class ServiceContractUpdate(BaseModel):
    """서비스 계약 수정 요청 스키마."""

    customer_id: str | None = None
    contract_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal | None = None
    is_active: bool | None = None


class ServiceContract(BaseDocument):
    """서비스 계약 문서."""

    customer_id: str = ""
    contract_type: str = ""
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal = Decimal(0)
    is_active: bool = True
