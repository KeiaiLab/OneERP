"""견적요청(RequestForQuotation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal  # noqa: TC003 — pydantic model_json_schema 런타임 필요

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class RFQItem(LineItem):
    """견적요청 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal


class RequestForQuotationCreate(BaseModel):
    """견적요청 생성 요청 스키마."""

    transaction_date: date | None = None
    suppliers: list[str] = []
    items: list[RFQItem] = []


class RequestForQuotationUpdate(BaseModel):
    """견적요청 수정 요청 스키마."""

    transaction_date: date | None = None
    suppliers: list[str] | None = None
    items: list[RFQItem] | None = None


class RequestForQuotation(BaseDocument):
    """견적요청 문서 — 복수 공급업체에 견적을 요청.

    naming prefix: RFQ
    """

    transaction_date: date | None = None
    suppliers: list[str] = []
    items: list[RFQItem] = []
