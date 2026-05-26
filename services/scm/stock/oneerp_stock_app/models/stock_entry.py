"""재고이동(StockEntry) 모델 정의.

L2 비즈니스 룰 매핑:
- BR-STK-011: entry_type 구분 (receipt/issue/transfer/manufacture/scrap)
- BR-STK-019: 위험물 관리 (hazardous 품목 특수 처리)
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class StockEntryType(StrEnum):
    """재고이동 유형."""

    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    MANUFACTURE = "manufacture"
    SCRAP = "scrap"


class StockEntryItem(LineItem):
    """재고이동 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    source_warehouse: str | None = Field(default=None, description="출고 창고")
    target_warehouse: str | None = Field(default=None, description="입고 창고")
    valuation_rate: Decimal = Field(default=Decimal(0), description="평가 단가")


class StockEntry(BaseDocument):
    """재고이동 문서 — 입고/출고/이동/제조입고/폐기."""

    entry_id: str = Field(description="재고이동 ID")
    entry_type: StockEntryType = Field(description="재고이동 유형")
    posting_date: str = Field(description="전기일자")
    items: list[StockEntryItem] = Field(
        default_factory=list, description="재고이동 라인 아이템 목록"
    )
    remarks: str | None = Field(default=None, description="비고")


class StockEntryCreate(BaseModel):
    """재고이동 생성 요청 스키마."""

    entry_type: StockEntryType
    posting_date: str
    items: list[StockEntryItem] = []
    remarks: str | None = None


class StockEntryUpdate(BaseModel):
    """재고이동 수정 요청 스키마 — 모든 필드 선택적."""

    entry_type: StockEntryType | None = None
    posting_date: str | None = None
    items: list[StockEntryItem] | None = None
    remarks: str | None = None
