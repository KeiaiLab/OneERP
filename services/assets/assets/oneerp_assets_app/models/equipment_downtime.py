"""장비 비가동(EquipmentDowntime) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class EquipmentDowntimeCreate(BaseModel):
    """장비 비가동 생성 요청 스키마."""

    asset_id: str
    start_date: date | None = None
    end_date: date | None = None
    duration_hours: Decimal = Decimal(0)
    reason: str = ""
    impact: str = ""


class EquipmentDowntimeUpdate(BaseModel):
    """장비 비가동 수정 요청 스키마."""

    asset_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_hours: Decimal | None = None
    reason: str | None = None
    impact: str | None = None


class EquipmentDowntime(BaseDocument):
    """장비 비가동 문서."""

    asset_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    duration_hours: Decimal = Decimal(0)
    reason: str = ""
    impact: str = ""
