"""반품 승인(ReturnMerchandiseAuthorization) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ReturnMerchandiseAuthorizationCreate(BaseModel):
    """반품 승인 생성 요청 스키마."""

    customer_id: str
    sales_order_id: str = ""
    reason: str = ""
    return_date: date | None = None
    refund_amount: Decimal = Decimal(0)


class ReturnMerchandiseAuthorizationUpdate(BaseModel):
    """반품 승인 수정 요청 스키마."""

    customer_id: str | None = None
    sales_order_id: str | None = None
    reason: str | None = None
    return_date: date | None = None
    refund_amount: Decimal | None = None


class ReturnMerchandiseAuthorization(BaseDocument):
    """반품 승인 문서."""

    customer_id: str = ""
    sales_order_id: str = ""
    reason: str = ""
    return_date: date | None = None
    refund_amount: Decimal = Decimal(0)
