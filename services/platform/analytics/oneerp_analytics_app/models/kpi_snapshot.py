"""KPI 스냅샷(KPISnapshot) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KPISnapshotCreate(BaseModel):
    """KPI 스냅샷 생성 요청 스키마."""

    kpi_id: str
    period: str = ""
    actual_value: Decimal = Decimal(0)
    target_value: Decimal = Decimal(0)
    achievement_rate: Decimal = Decimal(0)


class KPISnapshotUpdate(BaseModel):
    """KPI 스냅샷 수정 요청 스키마."""

    kpi_id: str | None = None
    period: str | None = None
    actual_value: Decimal | None = None
    target_value: Decimal | None = None
    achievement_rate: Decimal | None = None


class KPISnapshot(BaseDocument):
    """KPI 스냅샷 문서."""

    kpi_id: str = ""
    period: str = ""
    actual_value: Decimal = Decimal(0)
    target_value: Decimal = Decimal(0)
    achievement_rate: Decimal = Decimal(0)
