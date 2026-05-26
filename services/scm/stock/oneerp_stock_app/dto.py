"""stock 서비스 DTO 집약 (OE004).

route/service 계층에서 사용하는 요청/응답 스키마를 여기에 모은다.
models/ 하위는 Document(영속 엔티티) 정의만 담당한다.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from oneerp_stock_app.models.purchase_receipt import PurchaseReceiptItem


class ItemCreate(BaseModel):
    """품목 생성 요청 스키마."""

    item_code: str | None = None
    item_name: str
    item_group: str
    stock_uom: str = "EA"
    is_stock_item: bool = True
    has_batch_no: bool = False
    has_serial_no: bool = False
    valuation_method: str = "FIFO"
    default_warehouse: str | None = None
    reorder_level: Decimal = Field(default=Decimal(0))


class ItemUpdate(BaseModel):
    """품목 수정 요청 스키마 — 모든 필드 선택적."""

    item_name: str | None = None
    item_group: str | None = None
    stock_uom: str | None = None
    is_stock_item: bool | None = None
    has_batch_no: bool | None = None
    has_serial_no: bool | None = None
    valuation_method: str | None = None
    default_warehouse: str | None = None
    reorder_level: Decimal | None = None


class PurchaseReceiptItemInput(BaseModel):
    """입고전표 라인 생성/수정용 입력 스키마."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(default="", description="품목명")
    qty: float = Field(description="수량")
    rate: float = Field(default=0.0, description="단가")
    warehouse: str = Field(default="", description="입고 창고")


class PurchaseReceiptCreate(BaseModel):
    """입고전표 생성 요청."""

    supplier_name: str = ""
    posting_date: str | None = None
    purchase_order_id: str | None = None
    items: list[PurchaseReceiptItemInput] = Field(default_factory=list)


class PurchaseReceiptUpdate(BaseModel):
    """입고전표 수정 요청 — 모든 필드 선택적."""

    supplier_name: str | None = None
    posting_date: str | None = None
    purchase_order_id: str | None = None
    items: list[PurchaseReceiptItemInput] | None = None


# PurchaseReceiptItem 재노출 — 모델 측 라인 구조를 dto 계층에서도 참조 가능하도록.
__all__ = [
    "ItemCreate",
    "ItemUpdate",
    "PurchaseReceiptCreate",
    "PurchaseReceiptItem",
    "PurchaseReceiptItemInput",
    "PurchaseReceiptUpdate",
]
