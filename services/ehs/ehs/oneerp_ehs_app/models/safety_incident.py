"""안전 사고 보고(SafetyIncident) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date, datetime


class IncidentType(StrEnum):
    """사고 유형."""

    INJURY = "injury"
    NEAR_MISS = "near_miss"
    PROPERTY_DAMAGE = "property_damage"
    ENVIRONMENTAL = "environmental"


class Severity(StrEnum):
    """심각도."""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    FATAL = "fatal"


class IncidentStatus(StrEnum):
    """사고 상태."""

    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SafetyIncidentCreate(BaseModel):
    """안전 사고 보고 생성 요청 스키마."""

    incident_date: datetime
    location: str
    incident_type: IncidentType
    severity: Severity
    employee: str | None = None
    description: str
    root_cause: str | None = None
    corrective_action: str | None = None
    reported_to_kosha: bool = False
    kosha_report_date: date | None = None
    investigation_team: list[str] | None = None
    status: IncidentStatus = IncidentStatus.REPORTED


class SafetyIncidentUpdate(BaseModel):
    """안전 사고 보고 수정 요청 스키마."""

    incident_date: datetime | None = None
    location: str | None = None
    incident_type: IncidentType | None = None
    severity: Severity | None = None
    employee: str | None = None
    description: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    reported_to_kosha: bool | None = None
    kosha_report_date: date | None = None
    investigation_team: list[str] | None = None
    status: IncidentStatus | None = None


class SafetyIncident(BaseDocument):
    """안전 사고 보고 문서."""

    incident_date: datetime | None = None
    location: str = ""
    incident_type: IncidentType = IncidentType.NEAR_MISS
    severity: Severity = Severity.MINOR
    employee: str | None = None
    description: str = ""
    root_cause: str | None = None
    corrective_action: str | None = None
    reported_to_kosha: bool = False
    kosha_report_date: date | None = None
    investigation_team: list[str] | None = None
    status: IncidentStatus = IncidentStatus.REPORTED
