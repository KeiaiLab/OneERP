"""구매입고(Purchase Receipt) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class PurchaseReceiptItem(LineItem):
    """구매입고 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액")
    warehouse: str = Field(default="", description="입고 창고")
    purchase_order: str = Field(default="", description="참조 구매주문 ID")
    inspection_required: bool = Field(default=False, description="입고 품질검사 필요 여부")
    inspection_status: str = Field(default="not_required", description="입고 품질검사 상태")
    quality_inspection_id: str = Field(default="", description="연계된 품질검사 ID")


class PurchaseReceiptCreate(BaseModel):
    """구매입고 생성 요청 스키마."""

    supplier: str = ""
    supplier_name: str = ""
    posting_date: date | None = None
    items: list[PurchaseReceiptItem] = []
    warehouse: str = ""


class PurchaseReceiptUpdate(BaseModel):
    """구매입고 수정 요청 스키마."""

    supplier: str | None = None
    supplier_name: str | None = None
    posting_date: date | None = None
    items: list[PurchaseReceiptItem] | None = None
    warehouse: str | None = None


class PurchaseReceipt(BaseDocument):
    """구매입고 문서 — 공급업체로부터 자재를 입고받는 트랜잭션.

    naming prefix: PRCP
    """

    purchase_order_id: str = Field(default="", description="원본 구매주문 ID")
    supplier: str = Field(default="", description="공급업체 ID")
    supplier_name: str = Field(default="", description="공급업체명 (비정규화)")
    posting_date: date | None = Field(default=None, description="전기일자")
    items: list[PurchaseReceiptItem] = Field(
        default_factory=list, description="입고 라인 아이템 목록"
    )
    total_qty: Decimal = Field(default=Decimal(0), description="총 입고 수량")
    total_amount: Decimal = Field(default=Decimal(0), description="총 입고 금액")
    warehouse: str = Field(default="", description="기본 입고 창고")
    inspection_status: str = Field(default="not_required", description="헤더 품질검사 상태")
    quality_inspection_ids: list[str] = Field(
        default_factory=list, description="연계된 품질검사 ID 목록"
    )
