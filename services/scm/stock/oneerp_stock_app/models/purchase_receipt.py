"""입고전표(Purchase Receipt) 모델 정의.

stock 서비스 내에서 입고 전표를 직접 관리한다 (buying 서비스 의존 회피).
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PurchaseReceiptItem(BaseModel):
    """입고전표 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(default="", description="품목명")
    qty: float = Field(description="수량")
    rate: float = Field(default=0.0, description="단가")
    warehouse: str = Field(default="", description="입고 창고")
    amount: float = Field(default=0.0, description="금액 (qty * rate)")


class PurchaseReceipt(BaseDocument):
    """입고전표 마스터 문서."""

    supplier_name: str = Field(default="", description="공급업체명")
    posting_date: str | None = Field(default=None, description="입고일")
    purchase_order_id: str = Field(default="", description="연결된 구매주문 ID")
    items: list[PurchaseReceiptItem] = Field(default_factory=list, description="입고 라인")
    total_qty: float = Field(default=0.0, description="총 수량")
    total_amount: float = Field(default=0.0, description="총 금액")
