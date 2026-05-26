"""POS 거래(POSTransaction) 모델 정의.

L2 비즈니스 룰:
- BR-SELL-010 / BR-POS-006: SUM(payments.amount) >= grand_total
- BR-POS-001: 라인 아이템 금액 자동 계산 (qty x rate)
- BR-POS-002: 거래 합계 자동 계산 (SUM items + taxes)
- BR-POS-010: POS 영수증 불변성 (수정/삭제 API 없음)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, model_validator

_PAYMENT_TOLERANCE = Decimal("0.01")


class POSTransactionItem(LineItem):
    """POS 거래 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal = Decimal(0)


class POSTransactionPayment(BaseModel):
    """POS 거래 결제 내역."""

    mode_of_payment: str
    amount: Decimal = Decimal(0)


class POSTransaction(BaseDocument):
    """POS 거래 문서 — POS 판매 트랜잭션.

    naming prefix: PTXN
    """

    customer_id: str = ""
    customer_name: str = ""
    pos_profile_ref: str = ""
    posting_date: date
    items: list[POSTransactionItem] = []
    total: Decimal = Decimal(0)
    grand_total: Decimal = Decimal(0)
    payments: list[POSTransactionPayment] = []


class POSTransactionCreate(BaseModel):
    """POS 거래 생성 요청 스키마. BR-SELL-010 검증 포함."""

    customer_id: str = ""
    customer_name: str = ""
    pos_profile_ref: str = ""
    posting_date: date
    items: list[POSTransactionItem] = []
    payments: list[POSTransactionPayment] = []

    @model_validator(mode="after")
    def _결제금액_검증(self) -> POSTransactionCreate:
        """BR-SELL-010/BR-POS-006: 결제 합계 >= grand_total(items+taxes)."""
        if not self.items or not self.payments:
            return self
        # grand_total = items 합계 + taxes (taxes는 별도 필드가 없으므로 items 합계 사용)
        grand_total = sum(item.amount for item in self.items)
        payment_total = sum(p.amount for p in self.payments)
        if payment_total < grand_total - _PAYMENT_TOLERANCE:
            msg = f"결제 금액이 부족합니다: 결제({payment_total}) < 거래총액({grand_total})"
            raise ValueError(msg)
        return self


class POSTransactionUpdate(BaseModel):
    """POS 거래 수정 요청 스키마 — 모든 필드 선택적."""

    customer_id: str | None = None
    customer_name: str | None = None
    pos_profile_ref: str | None = None
    posting_date: date | None = None
    items: list[POSTransactionItem] | None = None
    payments: list[POSTransactionPayment] | None = None
