"""POS 마감(POSClosingEntry) 트랜잭션 모델.

L2 비즈니스 룰:
- BR-POS-008: POS 마감 시재 차이 계산
- BR-POS-009: POS 마감 매출 합계 자동 계산
- BR-POS-015: 마감 기간 중복 방지
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class POSClosingEntryCreate(BaseModel):
    """POS 마감 생성 요청 스키마."""

    pos_profile: str = ""
    period_start: datetime | None = None
    period_end: datetime | None = None
    opening_amount: Decimal = Decimal(0)
    closing_amount: Decimal = Decimal(0)
    total_sales: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)


class POSClosingEntryUpdate(BaseModel):
    """POS 마감 수정 요청 스키마."""

    pos_profile: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    opening_amount: Decimal | None = None
    closing_amount: Decimal | None = None
    total_sales: Decimal | None = None
    difference: Decimal | None = None


class POSClosingEntry(BaseDocument):
    """POS 마감 트랜잭션 — 영업일 POS 정산.

    naming prefix: POSC
    """

    pos_profile: str = ""
    period_start: datetime | None = None
    period_end: datetime | None = None
    opening_amount: Decimal = Decimal(0)
    closing_amount: Decimal = Decimal(0)
    total_sales: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)
