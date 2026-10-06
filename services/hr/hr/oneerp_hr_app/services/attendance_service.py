"""근태 서비스 — 주 52시간 준수와 모바일 출퇴근 워크벤치 로직."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_STANDARD_WEEKLY_HOURS = 40.0
_MAX_WEEKLY_HOURS = 52.0
_MAX_OVERTIME_WEEKLY_HOURS = 12.0
_SUPPORTED_CHANNELS = {"web", "mobile_widget", "kiosk"}
_LOCATION_REQUIRED_CHANNELS = {"mobile_widget", "kiosk"}


class AttendanceLocationValidationError(ValueError):
    """모바일 출퇴근 위치 증빙 검증 실패."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AttendanceService:
    """근태 관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._attendance_repo = Repository("attendances", tenant_id=tenant_id)

    @staticmethod
    def _ensure_datetime(value: str | datetime) -> datetime:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _scheduled_datetime(attendance_date: date | str, hhmm: str) -> datetime | None:
        if not hhmm:
            return None
        work_date = (
            date.fromisoformat(attendance_date)
            if isinstance(attendance_date, str)
            else attendance_date
        )
        hour_str, minute_str = hhmm.split(":", 1)
        return datetime(
            work_date.year,
            work_date.month,
            work_date.day,
            int(hour_str),
            int(minute_str),
            tzinfo=UTC,
        )

    @staticmethod
    def _normalize_location_capture(payload: dict[str, Any]) -> dict[str, Any]:
        channel = str(payload.get("capture_channel") or "web").strip().lower()
        if channel not in _SUPPORTED_CHANNELS:
            raise AttendanceLocationValidationError("ERR-HR-049", "지원하지 않는 출퇴근 채널입니다")

        gps_latitude = payload.get("gps_latitude")
        gps_longitude = payload.get("gps_longitude")
        has_partial_gps = (gps_latitude is None) != (gps_longitude is None)
        if has_partial_gps:
            raise AttendanceLocationValidationError(
                "ERR-HR-048",
                "GPS 좌표는 위도와 경도를 함께 전달해야 합니다",
            )

        has_gps = gps_latitude is not None and gps_longitude is not None
        has_ip = bool(payload.get("ip_address"))
        if channel in _LOCATION_REQUIRED_CHANNELS and not (has_ip or has_gps):
            raise AttendanceLocationValidationError(
                "ERR-HR-047",
                "모바일/키오스크 체크인은 IP 또는 GPS 정보가 필요합니다",
            )

        if has_gps and has_ip:
            proof_type = "gps+ip"
        elif has_gps:
            proof_type = "gps"
        elif has_ip:
            proof_type = "ip"
        else:
            proof_type = "none"

        location_status = "verified" if proof_type != "none" else "not_required"
        return {
            "capture_channel": channel,
            "ip_address": payload.get("ip_address", ""),
            "gps_latitude": gps_latitude,
            "gps_longitude": gps_longitude,
            "location_status": location_status,
            "location_proof_type": proof_type,
        }

    def build_check_in_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """체크인 입력을 저장용 payload로 정규화한다."""
        recorded_at = self._ensure_datetime(payload["recorded_at"])
        attendance_date = payload.get("attendance_date") or recorded_at.date().isoformat()
        scheduled_start = self._scheduled_datetime(
            attendance_date, payload.get("scheduled_start_time", "")
        )
        late_minutes = 0
        if scheduled_start is not None and recorded_at > scheduled_start:
            late_minutes = int((recorded_at - scheduled_start).total_seconds() // 60)

        location_capture = self._normalize_location_capture(payload)
        return {
            "employee_id": payload["employee_id"],
            "employee_name": payload.get("employee_name", ""),
            "department": payload.get("department", ""),
            "attendance_date": attendance_date,
            "status": payload.get("status", "present"),
            "shift_name": payload.get("shift_name", ""),
            "scheduled_start_time": payload.get("scheduled_start_time", ""),
            "scheduled_end_time": payload.get("scheduled_end_time", ""),
            "check_in_at": recorded_at,
            "late_minutes": late_minutes,
            "is_late": late_minutes > 0,
            "working_hours": 0.0,
            "early_leave_minutes": 0,
            "is_early_leave": False,
            **location_capture,
        }

    def build_check_out_payload(
        self,
        attendance: dict[str, Any],
        recorded_at: str | datetime,
    ) -> dict[str, Any]:
        """체크아웃 시 조퇴 여부와 실근무시간을 계산한다."""
        check_out_at = self._ensure_datetime(recorded_at)
        check_in_at = attendance.get("check_in_at")
        check_in_dt = self._ensure_datetime(check_in_at) if check_in_at else None

        working_hours = 0.0
        if check_in_dt is not None and check_out_at >= check_in_dt:
            working_hours = round((check_out_at - check_in_dt).total_seconds() / 3600, 2)

        scheduled_end = self._scheduled_datetime(
            attendance.get("attendance_date") or check_out_at.date().isoformat(),
            attendance.get("scheduled_end_time", ""),
        )
        early_leave_minutes = 0
        if scheduled_end is not None and check_out_at < scheduled_end:
            early_leave_minutes = int((scheduled_end - check_out_at).total_seconds() // 60)

        return {
            "check_out_at": check_out_at,
            "working_hours": working_hours,
            "early_leave_minutes": early_leave_minutes,
            "is_early_leave": early_leave_minutes > 0,
        }

    @staticmethod
    def build_location_summary(record: dict[str, Any]) -> dict[str, Any]:
        """모바일/키오스크 체크인용 위치 증빙 요약."""
        return {
            "capture_channel": record.get("capture_channel", "web"),
            "location_status": record.get("location_status", "not_required"),
            "location_proof_type": record.get("location_proof_type", "none"),
            "has_ip_address": bool(record.get("ip_address")),
            "has_gps_coordinates": record.get("gps_latitude") is not None
            and record.get("gps_longitude") is not None,
        }

    @classmethod
    def build_status_badge(cls, record: dict[str, Any]) -> str:
        """리스트/상세용 상태 배지."""
        status = record.get("status", "present")
        if status != "present":
            return status
        if record.get("check_in_at") and not record.get("check_out_at"):
            return "checked_in_late" if record.get("is_late") else "checked_in"
        if record.get("check_out_at"):
            if record.get("is_late") and record.get("is_early_leave"):
                return "late_and_early_leave"
            if record.get("is_late"):
                return "late_checked_out"
            if record.get("is_early_leave"):
                return "early_leave"
            return "completed"
        return "pending"

    @classmethod
    def build_available_actions(cls, record: dict[str, Any]) -> list[str]:
        """현재 기록에서 가능한 다음 액션."""
        actions = ["view_weekly_summary"]
        if (
            record.get("status") == "present"
            and record.get("check_in_at")
            and not record.get("check_out_at")
        ):
            actions.insert(0, "check_out")
        return actions

    @classmethod
    def build_attendance_view(cls, record: dict[str, Any]) -> dict[str, Any]:
        """근태 한 건에 워크벤치 전용 파생 필드를 추가한다."""
        public = dict(record)
        if "_id" in public:
            public["id"] = public["_id"]
        public["status_badge"] = cls.build_status_badge(record)
        public["location_summary"] = cls.build_location_summary(record)
        public["available_actions"] = cls.build_available_actions(record)
        return public

    @classmethod
    def build_workbench_summary(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        """근태 워크벤치 요약을 계산한다."""
        return {
            "present_count": sum(1 for record in records if record.get("status") == "present"),
            "late_count": sum(1 for record in records if record.get("is_late")),
            "early_leave_count": sum(1 for record in records if record.get("is_early_leave")),
            "checked_in_count": sum(
                1
                for record in records
                if record.get("status") == "present"
                and record.get("check_in_at")
                and not record.get("check_out_at")
            ),
            "checked_out_count": sum(1 for record in records if record.get("check_out_at")),
            "location_verified_count": sum(
                1 for record in records if record.get("location_status") == "verified"
            ),
            "mobile_widget_count": sum(
                1 for record in records if record.get("capture_channel") == "mobile_widget"
            ),
            "kiosk_count": sum(1 for record in records if record.get("capture_channel") == "kiosk"),
            "total_working_hours": round(
                sum(float(record.get("working_hours", 0) or 0) for record in records), 2
            ),
        }

    @classmethod
    def build_daily_report(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        """일일 근태 요약을 계산한다."""
        summary = cls.build_workbench_summary(records)
        summary.update(
            {
                "absent_count": sum(1 for record in records if record.get("status") == "absent"),
                "half_day_count": sum(
                    1 for record in records if record.get("status") == "half_day"
                ),
                "on_leave_count": sum(
                    1 for record in records if record.get("status") == "on_leave"
                ),
            }
        )
        return summary

    def check_weekly_work_hours(
        self,
        employee_id: str,
        week_start_date: str,
    ) -> dict[str, Any]:
        """BR-HR-002: 직원의 주간 근무시간을 집계하고 52시간 초과 여부를 반환한다."""
        start = date.fromisoformat(week_start_date)
        end = start + timedelta(days=6)

        records = self._attendance_repo.find_many(
            {
                "employee_id": employee_id,
                "attendance_date": {
                    "$gte": start,
                    "$lte": end,
                },
            },
            limit=1000,
        )

        total_hours = sum(float(r.get("working_hours", 0)) for r in records)
        overtime_hours = max(0.0, total_hours - _STANDARD_WEEKLY_HOURS)
        exceeded_52h = total_hours > _MAX_WEEKLY_HOURS
        exceeded_overtime_12h = overtime_hours > _MAX_OVERTIME_WEEKLY_HOURS

        if exceeded_52h:
            logger.warning(
                "주52시간 초과: 주간 %s, %.1f시간",
                week_start_date,
                total_hours,
            )
        if exceeded_overtime_12h:
            logger.warning(
                "연장근로 12시간 초과: 연장 %.1f시간",
                overtime_hours,
            )

        return {
            "employee": employee_id,
            "week_start": week_start_date,
            "week_end": end.isoformat(),
            "total_hours": total_hours,
            "overtime_hours": overtime_hours,
            "exceeded_52h": exceeded_52h,
            "exceeded_overtime_12h": exceeded_overtime_12h,
        }

    def check_health_checkup_due(
        self,
        employee_id: str,
        cycle_months: int = 12,
    ) -> dict[str, Any]:
        """BR-HR-017: 직원의 건강검진 주기 초과 여부를 확인한다."""
        checkup_repo = Repository("health_checkups", tenant_id=self._tenant_id)
        checkups = checkup_repo.find_many(
            {"employee_id": employee_id, "status": "completed"},
            limit=10000,
        )
        today = datetime.now(UTC).date()

        if not checkups:
            return {
                "employee": employee_id,
                "last_checkup_date": None,
                "due": True,
                "overdue_days": 0,
            }

        latest_date: date | None = None
        for chk in checkups:
            raw = chk.get("checkup_date")
            if not raw:
                continue
            chk_date = date.fromisoformat(str(raw)) if isinstance(raw, str) else raw
            if latest_date is None or chk_date > latest_date:
                latest_date = chk_date

        if latest_date is None:
            return {
                "employee": employee_id,
                "last_checkup_date": None,
                "due": True,
                "overdue_days": 0,
            }

        due_date = latest_date + timedelta(days=cycle_months * 30)
        overdue_days = max(0, (today - due_date).days)
        is_due = today >= due_date

        logger.info(
            "건강검진 주기 확인: 마지막 %s, 초과 %s",
            latest_date.isoformat(),
            is_due,
        )

        return {
            "employee": employee_id,
            "last_checkup_date": latest_date.isoformat(),
            "due": is_due,
            "overdue_days": overdue_days,
        }
