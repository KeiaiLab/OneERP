"""내부 통제(InternalControl) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ControlType(StrEnum):
    """통제 유형."""

    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class ControlFrequency(StrEnum):
    """통제 주기."""

    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ControlStatus(StrEnum):
    """통제 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class InternalControlCreate(BaseModel):
    """내부 통제 생성 요청 스키마."""

    control_id: str
    name: str
    description: str
    control_type: ControlType
    risk_area: str
    frequency: ControlFrequency
    responsible: str
    evidence_required: str | None = None
    status: ControlStatus = ControlStatus.DRAFT
    company: str = ""


class InternalControlUpdate(BaseModel):
    """내부 통제 수정 요청 스키마."""

    control_id: str | None = None
    name: str | None = None
    description: str | None = None
    control_type: ControlType | None = None
    risk_area: str | None = None
    frequency: ControlFrequency | None = None
    responsible: str | None = None
    evidence_required: str | None = None
    status: ControlStatus | None = None
    company: str | None = None


class InternalControl(BaseDocument):
    """내부 통제 문서."""

    control_id: str = ""
    name: str = ""
    description: str = ""
    control_type: ControlType = ControlType.PREVENTIVE
    risk_area: str = ""
    frequency: ControlFrequency = ControlFrequency.MONTHLY
    responsible: str = ""
    evidence_required: str | None = None
    status: ControlStatus = ControlStatus.DRAFT
    company: str = ""
