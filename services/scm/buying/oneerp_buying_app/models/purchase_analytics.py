"""구매분석(Purchase Analytics) 리포트 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PurchaseAnalyticsCreate(BaseModel):
    """구매분석 리포트 생성 요청 스키마."""

    period: str
    item_code: str = ""
    supplier: str = ""
    total_qty: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)


class PurchaseAnalyticsUpdate(BaseModel):
    """구매분석 리포트 수정 요청 스키마."""

    period: str | None = None
    item_code: str | None = None
    supplier: str | None = None
    total_qty: Decimal | None = None
    total_amount: Decimal | None = None


class PurchaseAnalytics(BaseDocument):
    """구매분석 리포트 — 읽기 전용 집계 뷰.

    naming prefix: PANA
    """

    period: str = ""
    item_code: str = ""
    supplier: str = ""
    total_qty: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
