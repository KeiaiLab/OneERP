"""타임시트(Timesheet) 모델 정의."""

from __future__ import annotations

from datetime import date as DateType  # noqa: TC003 — Pydantic v2 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class TimesheetLog(LineItem):
    """타임시트 로그 라인 — 시간 기록 항목."""

    date: DateType | None = None
    project_ref: str = ""
    task_ref: str = ""
    hours: Decimal = Decimal(0)
    activity_type: str = ""


class Timesheet(BaseDocument):
    """타임시트 문서 — 직원 시간 기록.

    naming prefix: TS
    """

    employee_id: str
    employee_name: str
    start_date: DateType
    end_date: DateType
    total_hours: Decimal = Decimal(0)
    time_logs: list[TimesheetLog] = []


class TimesheetCreate(BaseModel):
    """타임시트 생성 요청 스키마."""

    employee_id: str
    employee_name: str
    start_date: DateType
    end_date: DateType
    total_hours: Decimal = Decimal(0)
    time_logs: list[TimesheetLog] = []


class TimesheetUpdate(BaseModel):
    """타임시트 수정 요청 스키마 — 모든 필드 선택적."""

    employee_id: str | None = None
    employee_name: str | None = None
    start_date: DateType | None = None
    end_date: DateType | None = None
    total_hours: Decimal | None = None
    time_logs: list[TimesheetLog] | None = None
