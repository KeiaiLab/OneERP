"""서비스 기사(ServiceTechnician) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ServiceTechnicianCreate(BaseModel):
    """서비스 기사 생성 요청 스키마."""

    technician_name: str
    employee_id: str = ""
    specialization: str = ""
    is_available: bool = True
    rating: Decimal = Decimal(0)


class ServiceTechnicianUpdate(BaseModel):
    """서비스 기사 수정 요청 스키마."""

    technician_name: str | None = None
    employee_id: str | None = None
    specialization: str | None = None
    is_available: bool | None = None
    rating: Decimal | None = None


class ServiceTechnician(BaseDocument):
    """서비스 기사 문서."""

    technician_name: str = ""
    employee_id: str = ""
    specialization: str = ""
    is_available: bool = True
    rating: Decimal = Decimal(0)
