"""부산물(ByProduct) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ByProductCreate(BaseModel):
    """부산물 생성 요청 스키마."""

    work_order_id: str
    item_code: str = ""
    qty: Decimal = Decimal(0)
    warehouse_id: str = ""


class ByProductUpdate(BaseModel):
    """부산물 수정 요청 스키마."""

    work_order_id: str | None = None
    item_code: str | None = None
    qty: Decimal | None = None
    warehouse_id: str | None = None


class ByProduct(BaseDocument):
    """부산물 문서."""

    work_order_id: str = ""
    item_code: str = ""
    qty: Decimal = Decimal(0)
    warehouse_id: str = ""
