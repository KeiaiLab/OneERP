"""고장신고(BreakdownReport) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class BreakdownSeverity(StrEnum):
    """고장 심각도."""

    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class BreakdownReportStatus(StrEnum):
    """고장신고 상태."""

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    WORK_ORDER_CREATED = "work_order_created"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BreakdownReportCreate(BaseModel):
    """고장신고 생성 요청 스키마."""

    equipment_id: str
    reported_by: str = ""
    failure_mode: str = ""
    severity: BreakdownSeverity = BreakdownSeverity.MAJOR
    description: str = ""
    reported_at: datetime | None = None


class BreakdownReportUpdate(BaseModel):
    """고장신고 수정 요청 스키마."""

    equipment_id: str | None = None
    reported_by: str | None = None
    failure_mode: str | None = None
    severity: BreakdownSeverity | None = None
    status: BreakdownReportStatus | None = None
    description: str | None = None
    reported_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    work_order_id: str | None = None


class BreakdownReport(BaseDocument):
    """고장신고 문서."""

    equipment_id: str = ""
    reported_by: str = ""
    failure_mode: str = ""
    severity: BreakdownSeverity = BreakdownSeverity.MAJOR
    status: BreakdownReportStatus = BreakdownReportStatus.REPORTED
    description: str = ""
    reported_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    work_order_id: str = ""
