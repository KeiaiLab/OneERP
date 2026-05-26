"""부대비용전표(LandedCostVoucher) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class LandedCostItem(LineItem):
    """부대비용 라인 아이템."""

    description: str
    tax_amount: Decimal = Decimal(0)
    allocation_method: str = "qty"


class LandedCostVoucherCreate(BaseModel):
    """부대비용전표 생성 요청 스키마."""

    receipt_document: str
    posting_date: date | None = None
    items: list[LandedCostItem] = []


class LandedCostVoucherUpdate(BaseModel):
    """부대비용전표 수정 요청 스키마."""

    receipt_document: str | None = None
    posting_date: date | None = None
    items: list[LandedCostItem] | None = None


class LandedCostVoucher(BaseDocument):
    """부대비용전표 문서 — 입고 관련 부대비용 배분.

    naming prefix: LCV
    """

    receipt_document: str = ""
    posting_date: date | None = None
    items: list[LandedCostItem] = []
    total: Decimal = Decimal(0)
