"""영업 사원(SalesPerson) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SalesPersonCreate(BaseModel):
    """영업 사원 생성 요청 스키마."""

    person_name: str
    employee_id: str = ""
    commission_rate: Decimal = Decimal(0)
    is_active: bool = True


class SalesPersonUpdate(BaseModel):
    """영업 사원 수정 요청 스키마."""

    person_name: str | None = None
    employee_id: str | None = None
    commission_rate: Decimal | None = None
    is_active: bool | None = None


class SalesPerson(BaseDocument):
    """영업 사원 문서."""

    person_name: str = ""
    employee_id: str = ""
    commission_rate: Decimal = Decimal(0)
    is_active: bool = True
