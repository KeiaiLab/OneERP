"""BOM 트리(BomTree) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BomTreeCreate(BaseModel):
    """BOM 트리 생성 요청 스키마."""

    parent_bom_id: str
    child_item_code: str = ""
    qty: Decimal = Decimal(0)
    level: int = 0
    uom: str = ""


class BomTreeUpdate(BaseModel):
    """BOM 트리 수정 요청 스키마."""

    parent_bom_id: str | None = None
    child_item_code: str | None = None
    qty: Decimal | None = None
    level: int | None = None
    uom: str | None = None


class BOMTree(BaseDocument):
    """BOM 트리 문서."""

    parent_bom_id: str = ""
    child_item_code: str = ""
    qty: Decimal = Decimal(0)
    level: int = 0
    uom: str = ""
