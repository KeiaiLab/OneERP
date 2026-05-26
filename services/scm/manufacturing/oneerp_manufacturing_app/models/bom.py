"""BOM(Bill of Materials) 모델 정의.

L2 비즈니스 룰: BR-MFG-001 (품목 필수), BR-MFG-002 (기본수량 1.0), BR-MFG-003 (기본BOM 유일성).
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class BOMItem(LineItem):
    """BOM 라인 아이템 — 구성 자재."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(default=Decimal(0), description="단가")


class BOM(BaseDocument):
    """BOM 문서 — 자재 명세서.

    naming prefix: BOM
    """

    item_code: str = Field(description="완제품 품목 코드")
    item_name: str = Field(description="완제품 품목명")
    quantity: Decimal = Field(default=Decimal(1), description="기준 생산 수량")
    items: list[BOMItem] = Field(default_factory=list, description="BOM 구성 자재 목록")
    is_active: bool = Field(default=True, description="활성 여부")
    is_default: bool = Field(default=False, description="기본 BOM 여부")


class BOMCreate(BaseModel):
    """BOM 생성 요청 스키마."""

    item_code: str
    item_name: str
    quantity: Decimal = Decimal(1)
    items: list[BOMItem] = []
    is_active: bool = True
    is_default: bool = False


class BOMUpdate(BaseModel):
    """BOM 수정 요청 스키마 — 모든 필드 선택적."""

    item_code: str | None = None
    item_name: str | None = None
    quantity: Decimal | None = None
    items: list[BOMItem] | None = None
    is_active: bool | None = None
    is_default: bool | None = None
