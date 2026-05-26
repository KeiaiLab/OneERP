"""보전유형(MaintenanceType) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class MaintenanceTypeCreate(BaseModel):
    """보전유형 생성 요청 스키마."""

    type_name: str
    type_code: str = ""
    category: str = "corrective"
    description: str = ""
    default_priority: str = "medium"
    estimated_hours: float = 0.0


class MaintenanceTypeUpdate(BaseModel):
    """보전유형 수정 요청 스키마."""

    type_name: str | None = None
    type_code: str | None = None
    category: str | None = None
    description: str | None = None
    default_priority: str | None = None
    estimated_hours: float | None = None


class MaintenanceType(BaseDocument):
    """보전유형 문서."""

    type_name: str = ""
    type_code: str = ""
    category: str = "corrective"
    description: str = ""
    default_priority: str = "medium"
    estimated_hours: float = 0.0
