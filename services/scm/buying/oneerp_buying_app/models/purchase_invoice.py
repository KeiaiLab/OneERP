"""구매송장(Purchase Invoice) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-BUY-009: 미지급금 초기값 (outstanding_amount = grand_total)
- BR-BUY-016: PURCHASE_INVOICE_SUBMITTED 이벤트 (라우트에서 발행)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class PurchaseInvoiceItem(LineItem):
    """구매송장 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")


class PurchaseInvoiceTax(BaseModel):
    """구매송장 세금 항목."""

    tax_type: str
    rate: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)


class PurchaseInvoiceCreate(BaseModel):
    """구매송장 생성 요청 스키마."""

    supplier_id: str
    supplier_name: str
    posting_date: date
    due_date: date
    items: list[PurchaseInvoiceItem] = []
    taxes: list[PurchaseInvoiceTax] = []
    etax_invoice_ref: str | None = None


class PurchaseInvoiceUpdate(BaseModel):
    """구매송장 수정 요청 스키마."""

    supplier_id: str | None = None
    supplier_name: str | None = None
    posting_date: date | None = None
    due_date: date | None = None
    items: list[PurchaseInvoiceItem] | None = None
    taxes: list[PurchaseInvoiceTax] | None = None
    etax_invoice_ref: str | None = None


class PurchaseInvoice(BaseDocument):
    """구매송장 문서 — 공급업체로부터 받은 세금계산서/청구서.

    naming prefix: PI
    """

    purchase_order_id: str = Field(default="", description="원본 구매주문 ID")
    purchase_receipt_id: str = Field(default="", description="원본 구매입고 ID")
    supplier_id: str = Field(default="", description="공급업체 ID")
    supplier_name: str = Field(default="", description="공급업체명 (비정규화)")
    posting_date: date | None = Field(default=None, description="전기일자")
    due_date: date | None = Field(default=None, description="결제 기한")
    items: list[PurchaseInvoiceItem] = Field(
        default_factory=list, description="송장 라인 아이템 목록"
    )
    taxes: list[PurchaseInvoiceTax] = Field(default_factory=list, description="세금 항목 목록")
    net_total: Decimal = Field(default=Decimal(0), description="세전 총 금액")
    grand_total: Decimal = Field(default=Decimal(0), description="세후 총 금액")
    outstanding_amount: Decimal = Field(default=Decimal(0), description="미지급금 잔액")
    etax_invoice_ref: str | None = Field(default=None, description="전자세금계산서 참조 번호")
