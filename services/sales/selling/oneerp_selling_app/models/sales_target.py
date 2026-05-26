"""영업 목표(SalesTarget) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SalesTargetCreate(BaseModel):
    """영업 목표 생성 요청 스키마."""

    sales_person_id: str
    target_amount: Decimal = Decimal(0)
    achieved_amount: Decimal = Decimal(0)
    period: str = ""
    item_group: str = ""


class SalesTargetUpdate(BaseModel):
    """영업 목표 수정 요청 스키마."""

    sales_person_id: str | None = None
    target_amount: Decimal | None = None
    achieved_amount: Decimal | None = None
    period: str | None = None
    item_group: str | None = None


class SalesTarget(BaseDocument):
    """영업 목표 문서."""

    sales_person_id: str = ""
    target_amount: Decimal = Decimal(0)
    achieved_amount: Decimal = Decimal(0)
    period: str = ""
    item_group: str = ""
