"""차량 배정(VehicleAssignment) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class VehicleAssignmentCreate(BaseModel):
    """차량 배정 생성 요청 스키마."""

    vehicle_id: str
    employee_id: str = ""
    assignment_date: date | None = None
    return_date: date | None = None
    purpose: str = ""


class VehicleAssignmentUpdate(BaseModel):
    """차량 배정 수정 요청 스키마."""

    vehicle_id: str | None = None
    employee_id: str | None = None
    assignment_date: date | None = None
    return_date: date | None = None
    purpose: str | None = None


class VehicleAssignment(BaseDocument):
    """차량 배정 문서."""

    vehicle_id: str = ""
    employee_id: str = ""
    assignment_date: date | None = None
    return_date: date | None = None
    purpose: str = ""
