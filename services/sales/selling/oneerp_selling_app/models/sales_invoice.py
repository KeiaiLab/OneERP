"""판매송장(Sales Invoice) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class SalesInvoiceItem(LineItem):
    """판매송장 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")


class SalesInvoiceTax(BaseModel):
    """판매송장 세금 항목."""

    tax_type: str
    rate: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)


class SalesInvoice(BaseDocument):
    """판매송장 문서 — 고객에게 발행하는 세금계산서/청구서.

    naming prefix: SINV
    """

    customer_id: str = Field(default="", description="고객 ID")
    customer_name: str = Field(default="", description="고객명 (비정규화)")
    sales_partner_id: str = Field(default="", description="판매 파트너 ID 스냅샷")
    sales_partner_name: str = Field(default="", description="판매 파트너명 스냅샷")
    sales_partner_commission_rate: Decimal = Field(
        default=Decimal(0),
        description="판매 파트너 수수료율 스냅샷",
    )
    posting_date: date | None = Field(default=None, description="전기일자")
    due_date: date | None = Field(default=None, description="결제 기한")
    sales_order_ref: str | None = Field(default=None, description="판매주문 참조 ID")
    delivery_note_ref: str | None = Field(default=None, description="납품서 참조 ID")
    items: list[SalesInvoiceItem] = Field(default_factory=list, description="송장 라인 아이템 목록")
    taxes: list[SalesInvoiceTax] = Field(default_factory=list, description="세금 항목 목록")
    net_total: Decimal = Field(default=Decimal(0), description="세전 순 합계 (items.amount 합)")
    grand_total: Decimal = Field(default=Decimal(0), description="세후 총 금액")
    outstanding_amount: Decimal = Field(default=Decimal(0), description="미수금 잔액")
    etax_invoice_ref: str | None = Field(default=None, description="전자세금계산서 참조 번호")


_SALES_INVOICE_TYPES = {"date": __import__("datetime").date}

SalesInvoice.model_rebuild(_types_namespace=_SALES_INVOICE_TYPES)
