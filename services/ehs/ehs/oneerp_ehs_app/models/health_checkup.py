"""건강검진 관리(HealthCheckup) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CheckupType(StrEnum):
    """검진 유형."""

    GENERAL = "general"
    SPECIAL = "special"
    PRE_PLACEMENT = "pre_placement"


class ResultSummary(StrEnum):
    """검진 결과 요약."""

    NORMAL = "normal"
    OBSERVATION = "observation"
    FOLLOW_UP = "follow_up"
    ABNORMAL = "abnormal"


class CheckupStatus(StrEnum):
    """검진 상태."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FOLLOW_UP = "follow_up"


class HealthCheckupCreate(BaseModel):
    """건강검진 생성 요청 스키마."""

    employee: str
    checkup_type: CheckupType
    scheduled_date: date
    hospital: str | None = None
    completed_date: date | None = None
    result_summary: ResultSummary | None = None
    abnormal_findings: str | None = None
    follow_up_action: str | None = None
    next_checkup_date: date | None = None
    status: CheckupStatus = CheckupStatus.SCHEDULED


class HealthCheckupUpdate(BaseModel):
    """건강검진 수정 요청 스키마."""

    employee: str | None = None
    checkup_type: CheckupType | None = None
    scheduled_date: date | None = None
    hospital: str | None = None
    completed_date: date | None = None
    result_summary: ResultSummary | None = None
    abnormal_findings: str | None = None
    follow_up_action: str | None = None
    next_checkup_date: date | None = None
    status: CheckupStatus | None = None


class HealthCheckup(BaseDocument):
    """건강검진 문서."""

    employee: str = ""
    checkup_type: CheckupType = CheckupType.GENERAL
    scheduled_date: date | None = None
    hospital: str | None = None
    completed_date: date | None = None
    result_summary: ResultSummary | None = None
    abnormal_findings: str | None = None
    follow_up_action: str | None = None
    next_checkup_date: date | None = None
    status: CheckupStatus = CheckupStatus.SCHEDULED
