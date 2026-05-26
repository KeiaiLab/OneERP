"""출결(Attendance) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AttendanceStatus(StrEnum):
    """출결 상태."""

    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"


class AttendanceCreate(BaseModel):
    """출결 생성 요청 스키마."""

    employee_id: str
    employee_name: str = ""
    department: str = ""
    attendance_date: date
    status: AttendanceStatus = AttendanceStatus.PRESENT
    shift_name: str = ""
    scheduled_start_time: str = ""
    scheduled_end_time: str = ""
    capture_channel: str = "web"
    ip_address: str = ""
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    location_status: str = "not_required"
    location_proof_type: str = "none"
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    working_hours: float = 0.0
    late_minutes: int = 0
    early_leave_minutes: int = 0
    is_late: bool = False
    is_early_leave: bool = False


class AttendanceUpdate(BaseModel):
    """출결 수정 요청 스키마."""

    employee_name: str | None = None
    department: str | None = None
    attendance_date: date | None = None
    status: AttendanceStatus | None = None
    shift_name: str | None = None
    scheduled_start_time: str | None = None
    scheduled_end_time: str | None = None
    capture_channel: str | None = None
    ip_address: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    location_status: str | None = None
    location_proof_type: str | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    working_hours: float | None = None
    late_minutes: int | None = None
    early_leave_minutes: int | None = None
    is_late: bool | None = None
    is_early_leave: bool | None = None


class Attendance(BaseDocument):
    """출결 문서 — HR 근태 관리.

    naming prefix: ATT
    """

    employee_id: str = Field(default="", description="직원 ID")
    employee_name: str = Field(default="", description="직원명")
    department: str = Field(default="", description="부서")
    attendance_date: date | None = Field(default=None, description="출결일자")
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT, description="출결 상태")
    shift_name: str = Field(default="", description="교대명")
    scheduled_start_time: str = Field(default="", description="예정 출근 시각(HH:MM)")
    scheduled_end_time: str = Field(default="", description="예정 퇴근 시각(HH:MM)")
    capture_channel: str = Field(default="web", description="출근 채널(web/mobile_widget/kiosk)")
    ip_address: str = Field(default="", description="체크인 IP")
    gps_latitude: float | None = Field(default=None, description="체크인 GPS 위도")
    gps_longitude: float | None = Field(default=None, description="체크인 GPS 경도")
    location_status: str = Field(default="not_required", description="위치 검증 상태")
    location_proof_type: str = Field(default="none", description="위치 증빙 유형")
    check_in_at: datetime | None = Field(default=None, description="실제 출근 시각")
    check_out_at: datetime | None = Field(default=None, description="실제 퇴근 시각")
    working_hours: float = Field(default=0.0, description="실근무 시간")
    late_minutes: int = Field(default=0, description="지각 분")
    early_leave_minutes: int = Field(default=0, description="조퇴 분")
    is_late: bool = Field(default=False, description="지각 여부")
    is_early_leave: bool = Field(default=False, description="조퇴 여부")
