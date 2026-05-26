"""안전 사고(SafetyIncident) 문서 모델.

L2 비즈니스 룰: BR-HR-018 (안전사고 기록/보고).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SafetyIncidentStatus(StrEnum):
    """안전 사고 보고 상태."""

    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SafetyIncidentCreate(BaseModel):
    """안전 사고 생성 요청 스키마."""

    incident_date: date | None = None
    location: str = ""
    description: str = ""
    severity: str = ""
    employee_id: str = ""
    corrective_action: str = ""


class SafetyIncidentUpdate(BaseModel):
    """안전 사고 수정 요청 스키마."""

    incident_date: date | None = None
    location: str | None = None
    description: str | None = None
    severity: str | None = None
    employee_id: str | None = None
    corrective_action: str | None = None
    status: SafetyIncidentStatus | None = None


class SafetyIncident(BaseDocument):
    """안전 사고 문서."""

    status: SafetyIncidentStatus = Field(
        default=SafetyIncidentStatus.REPORTED,
        description="안전 사고 보고 상태",
    )
    incident_date: date | None = None
    location: str = ""
    description: str = ""
    severity: str = ""
    employee_id: str = ""
    corrective_action: str = ""
