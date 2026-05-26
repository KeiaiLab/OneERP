"""유지보수 일정(MaintenanceSchedule) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceScheduleCreate(BaseModel):
    """유지보수 일정 생성 요청 스키마."""

    asset_id: str
    schedule_name: str = ""
    frequency: str = ""
    last_maintenance: date | None = None
    next_maintenance: date | None = None
    is_active: bool = True


class MaintenanceScheduleUpdate(BaseModel):
    """유지보수 일정 수정 요청 스키마."""

    asset_id: str | None = None
    schedule_name: str | None = None
    frequency: str | None = None
    last_maintenance: date | None = None
    next_maintenance: date | None = None
    is_active: bool | None = None


class MaintenanceSchedule(BaseDocument):
    """유지보수 일정 문서."""

    asset_id: str = ""
    schedule_name: str = ""
    frequency: str = ""
    last_maintenance: date | None = None
    next_maintenance: date | None = None
    is_active: bool = True
