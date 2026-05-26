"""자산 수리(AssetRepair) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetRepairCreate(BaseModel):
    """자산 수리 생성 요청 스키마."""

    asset_id: str
    repair_date: date | None = None
    failure_description: str = ""
    repair_cost: Decimal = Decimal(0)
    vendor: str = ""
    is_completed: bool = False


class AssetRepairUpdate(BaseModel):
    """자산 수리 수정 요청 스키마."""

    asset_id: str | None = None
    repair_date: date | None = None
    failure_description: str | None = None
    repair_cost: Decimal | None = None
    vendor: str | None = None
    is_completed: bool | None = None


class AssetRepair(BaseDocument):
    """자산 수리 문서."""

    asset_id: str = ""
    repair_date: date | None = None
    failure_description: str = ""
    repair_cost: Decimal = Decimal(0)
    vendor: str = ""
    is_completed: bool = False
