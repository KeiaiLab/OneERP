"""자원 할당(ResourceAllocation) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ResourceAllocationCreate(BaseModel):
    """자원 할당 생성 요청 스키마."""

    project_id: str
    employee_id: str = ""
    allocation_percentage: Decimal = Decimal(100)
    start_date: date | None = None
    end_date: date | None = None


class ResourceAllocationUpdate(BaseModel):
    """자원 할당 수정 요청 스키마."""

    project_id: str | None = None
    employee_id: str | None = None
    allocation_percentage: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResourceAllocation(BaseDocument):
    """자원 할당 문서."""

    project_id: str = ""
    employee_id: str = ""
    allocation_percentage: Decimal = Decimal(100)
    start_date: date | None = None
    end_date: date | None = None
