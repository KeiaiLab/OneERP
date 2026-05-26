"""판매주문(Sales Order) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import Field


class SalesOrderItem(LineItem):
    """판매주문 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")


class SalesOrder(BaseDocument):
    """판매주문 문서 — 확정된 고객 주문.

    naming prefix: SO
    """

    customer_id: str = Field(default="", description="고객 ID")
    customer_name: str = Field(default="", description="고객명 (비정규화)")
    sales_partner_id: str = Field(default="", description="판매 파트너 ID 스냅샷")
    sales_partner_name: str = Field(default="", description="판매 파트너명 스냅샷")
    sales_partner_commission_rate: Decimal = Field(
        default=Decimal(0),
        description="판매 파트너 수수료율 스냅샷",
    )
    transaction_date: date | None = Field(default=None, description="거래일자")
    delivery_date: date | None = Field(default=None, description="납품 예정일")
    items: list[SalesOrderItem] = Field(default_factory=list, description="주문 라인 아이템 목록")
    total: Decimal = Field(default=Decimal(0), description="세전 합계 금액")
    grand_total: Decimal = Field(default=Decimal(0), description="세후 총 금액")
    source_quotation: str | None = Field(default=None, description="원본 견적서 참조 ID")
    downstream_refs: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "delivery_note_ids": [],
            "sales_invoice_ids": [],
        },
        description="후속 납품서/송장 추적",
    )


SalesOrder.model_rebuild(_types_namespace={"date": __import__("datetime").date})
