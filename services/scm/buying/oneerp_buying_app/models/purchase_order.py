"""구매주문(Purchase Order) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-BUY-008: 라인 합계 자동 계산 (amount=qty*rate, grand_total=total+taxes)
- BR-BUY-010: Draft만 수정/삭제 가능
- BR-BUY-011: 입고 수량 추적 (received_qty 누적)
- BR-BUY-014: 구매 가격 규칙 (PurchasePricingService)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class PurchaseOrderItem(LineItem):
    """구매주문 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")
    received_qty: Decimal = Field(default=Decimal(0), description="입고 수량")
    delivery_date: date | None = Field(default=None, description="라인별 납기일")


class PurchaseOrderCreate(BaseModel):
    """구매주문 생성 요청 스키마."""

    supplier_id: str
    supplier_name: str
    transaction_date: date
    items: list[PurchaseOrderItem] = []


class PurchaseOrderUpdate(BaseModel):
    """구매주문 수정 요청 스키마."""

    supplier_id: str | None = None
    supplier_name: str | None = None
    transaction_date: date | None = None
    items: list[PurchaseOrderItem] | None = None


class PurchaseOrder(BaseDocument):
    """구매주문 문서 — 공급업체에 대한 구매 요청.

    naming prefix: PO
    """

    supplier_id: str = Field(default="", description="공급업체 ID")
    supplier_name: str = Field(default="", description="공급업체명 (비정규화)")
    transaction_date: date | None = Field(default=None, description="거래일자")
    quotation_reference: str = Field(default="", description="원본 공급업체 견적 ID")
    items: list[PurchaseOrderItem] = Field(
        default_factory=list, description="구매주문 라인 아이템 목록"
    )
    total: Decimal = Field(default=Decimal(0), description="세전 합계 금액")
    grand_total: Decimal = Field(default=Decimal(0), description="세후 총 금액")
