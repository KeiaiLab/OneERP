"""납품서(Delivery Note) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import Field


class DeliveryNoteItem(LineItem):
    """납품서 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(default="", description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(default=Decimal(0), description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")
    warehouse: str = Field(default="", description="출고 창고")
    batch_no: str | None = Field(default=None, description="배치 번호")


class DeliveryNote(BaseDocument):
    """납품서 문서 — 고객에게 물품 인도를 기록.

    naming prefix: DN
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
    sales_order_ref: str | None = Field(default=None, description="판매주문 참조 ID")
    items: list[DeliveryNoteItem] = Field(default_factory=list, description="납품 라인 아이템 목록")
    transporter: str | None = Field(default=None, description="운송업체")
    downstream_refs: dict[str, list[str]] = Field(
        default_factory=lambda: {"sales_invoice_ids": []},
        description="후속 판매송장 추적",
    )
