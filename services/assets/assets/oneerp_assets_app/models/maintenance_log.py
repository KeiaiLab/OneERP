"""유지보수 로그(MaintenanceLog) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceLogCreate(BaseModel):
    """유지보수 로그 생성 요청 스키마."""

    asset_id: str
    log_date: date | None = None
    maintenance_type: str = ""
    description: str = ""
    cost: Decimal = Decimal(0)
    performed_by: str = ""


class MaintenanceLogUpdate(BaseModel):
    """유지보수 로그 수정 요청 스키마."""

    asset_id: str | None = None
    log_date: date | None = None
    maintenance_type: str | None = None
    description: str | None = None
    cost: Decimal | None = None
    performed_by: str | None = None


class MaintenanceLog(BaseDocument):
    """유지보수 로그 문서."""

    asset_id: str = ""
    log_date: date | None = None
    maintenance_type: str = ""
    description: str = ""
    cost: Decimal = Decimal(0)
    performed_by: str = ""
