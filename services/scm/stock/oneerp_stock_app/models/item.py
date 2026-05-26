"""품목(Item) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import Field


class Item(BaseDocument):
    """품목 마스터 — 재고 관리 대상 품목 정보."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    item_group: str = Field(description="품목 그룹")
    stock_uom: str = Field(default="EA", description="재고 단위")
    is_stock_item: bool = Field(default=True, description="재고 관리 대상 여부")
    has_batch_no: bool = Field(default=False, description="배치 번호 사용 여부")
    has_serial_no: bool = Field(default=False, description="시리얼 번호 사용 여부")
    valuation_method: str = Field(default="FIFO", description="재고 평가 방법")
    default_warehouse: str | None = Field(default=None, description="기본 창고")
    reorder_level: Decimal = Field(default=Decimal(0), description="재주문점")
