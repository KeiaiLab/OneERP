"""차량 배정(VehicleAssignment) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssignmentType(StrEnum):
    """배정 유형."""

    PERMANENT = "permanent"
    TEMPORARY = "temporary"
    POOL = "pool"


class AssignmentStatus(StrEnum):
    """배정 상태."""

    ACTIVE = "active"
    RETURNED = "returned"


class VehicleAssignmentCreate(BaseModel):
    """차량 배정 생성 요청 스키마."""

    vehicle: str
    employee: str
    department: str | None = None
    start_date: date
    end_date: date | None = None
    assignment_type: AssignmentType
    status: AssignmentStatus = AssignmentStatus.ACTIVE


class VehicleAssignmentUpdate(BaseModel):
    """차량 배정 수정 요청 스키마."""

    vehicle: str | None = None
    employee: str | None = None
    department: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    assignment_type: AssignmentType | None = None
    status: AssignmentStatus | None = None


class VehicleAssignment(BaseDocument):
    """차량 배정 문서."""

    vehicle: str = ""
    employee: str = ""
    department: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    assignment_type: AssignmentType = AssignmentType.TEMPORARY
    status: AssignmentStatus = AssignmentStatus.ACTIVE
