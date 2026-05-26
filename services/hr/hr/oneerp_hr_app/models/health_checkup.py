"""건강 검진(HealthCheckup) 문서 모델.

L2 비즈니스 룰: BR-HR-017 (건강검진 주기 관리).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class HealthCheckupStatus(StrEnum):
    """건강검진 관리 상태."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FOLLOW_UP = "follow_up"


class HealthCheckupCreate(BaseModel):
    """건강 검진 생성 요청 스키마."""

    employee_id: str
    checkup_date: date | None = None
    provider: str = ""
    result: str = ""
    next_checkup_date: date | None = None


class HealthCheckupUpdate(BaseModel):
    """건강 검진 수정 요청 스키마."""

    employee_id: str | None = None
    checkup_date: date | None = None
    provider: str | None = None
    result: str | None = None
    next_checkup_date: date | None = None
    status: HealthCheckupStatus | None = None


class HealthCheckup(BaseDocument):
    """건강 검진 문서."""

    status: HealthCheckupStatus = Field(
        default=HealthCheckupStatus.SCHEDULED,
        description="건강검진 관리 상태",
    )
    employee_id: str = ""
    checkup_date: date | None = None
    provider: str = ""
    result: str = ""
    next_checkup_date: date | None = None
