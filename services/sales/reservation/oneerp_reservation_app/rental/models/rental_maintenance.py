"""렌탈 유지보수(RentalMaintenance) 문서 모델.

렌탈 품목의 정비/수리 이력을 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceType(StrEnum):
    """유지보수 유형."""

    INSPECTION = "inspection"
    REPAIR = "repair"
    CLEANING = "cleaning"
    REPLACEMENT = "replacement"


class MaintenanceStatus(StrEnum):
    """유지보수 상태."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RentalMaintenanceCreate(BaseModel):
    """렌탈 유지보수 생성 요청 스키마."""

    rental_item_id: str
    maintenance_type: MaintenanceType = MaintenanceType.INSPECTION
    scheduled_date: date | None = None
    completed_date: date | None = None
    cost: Decimal = Decimal(0)
    description: str = ""
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    technician: str = ""


class RentalMaintenanceUpdate(BaseModel):
    """렌탈 유지보수 수정 요청 스키마."""

    rental_item_id: str | None = None
    maintenance_type: MaintenanceType | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    cost: Decimal | None = None
    description: str | None = None
    status: MaintenanceStatus | None = None
    technician: str | None = None


class RentalMaintenance(BaseDocument):
    """렌탈 유지보수 문서.

    유지보수 유형, 일정, 비용, 담당 기술자 정보를 포함한다.
    """

    rental_item_id: str = ""
    maintenance_type: MaintenanceType = MaintenanceType.INSPECTION
    scheduled_date: date | None = None
    completed_date: date | None = None
    cost: Decimal = Decimal(0)
    description: str = ""
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    technician: str = ""
