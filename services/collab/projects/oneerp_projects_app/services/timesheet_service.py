"""타임시트 서비스 — 제출, 인보이싱, 일괄 청구.

L2 비즈니스 룰 매핑:
- BR-PROJ-005: 타임시트 수정은 초안 상태에서만
- BR-PROJ-006: 타임시트 제출 시 총 근무시간 > 0
- BR-PROJ-015: 타임시트 인보이스 금액 = total_hours x hourly_rate
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class TimesheetService:
    """타임시트 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._ts_repo = Repository("timesheets", tenant_id=tenant_id)
        self._billing_repo = Repository("project_billings", tenant_id=tenant_id)
        self._task_repo = Repository("tasks", tenant_id=tenant_id)
        self._activity_type_repo = Repository("activity_types", tenant_id=tenant_id)

    @staticmethod
    def _coerce_date(value: Any) -> DateType | None:
        """문자열/날짜 입력을 date 객체로 정규화한다."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, DateType):
            return value
        try:
            return datetime.fromisoformat(str(value)).date()
        except ValueError:
            return None

    @staticmethod
    def validate_date_range(
        start_date: Any, end_date: Any
    ) -> tuple[DateType | None, DateType | None]:
        """타임시트 기간이 올바른지 검증한다."""
        normalized_start = TimesheetService._coerce_date(start_date)
        normalized_end = TimesheetService._coerce_date(end_date)
        if normalized_start and normalized_end and normalized_end < normalized_start:
            raise_unprocessable("ERR-PRJ-016", "종료일은 시작일보다 빠를 수 없습니다")
        return normalized_start, normalized_end

    @staticmethod
    def _validate_time_logs(
        time_logs: list[dict[str, Any]],
        *,
        start_date: DateType | None,
        end_date: DateType | None,
        require_dates: bool,
    ) -> None:
        """타임시트 라인 아이템의 날짜/시간 무결성을 검증한다."""
        for log in time_logs:
            hours = Decimal(str(log.get("hours", 0)))
            if hours <= 0:
                raise_unprocessable("ERR-PRJ-017", "각 time_log의 hours는 0보다 커야 합니다")
            work_date = TimesheetService._coerce_date(log.get("date"))
            if require_dates and work_date is None:
                raise_unprocessable(
                    "ERR-PRJ-018", "제출 전에 모든 time_logs에 작업일자를 입력해야 합니다"
                )
            if work_date and start_date and end_date and not (start_date <= work_date <= end_date):
                raise_unprocessable("ERR-PRJ-019", "작업일자는 타임시트 기간 안에 있어야 합니다")

    @staticmethod
    def validate_submission_document(
        timesheet: dict[str, Any],
    ) -> tuple[Decimal, list[dict[str, Any]]]:
        """제출 가능한 타임시트인지 검증하고 총 시간을 반환한다."""
        start_date, end_date = TimesheetService.validate_date_range(
            timesheet.get("start_date"),
            timesheet.get("end_date"),
        )
        total_hours = Decimal(str(timesheet.get("total_hours", 0)))
        if total_hours <= 0:
            raise_unprocessable(
                "ERR-PRJ-008",
                "총 근무시간이 0보다 커야 제출할 수 있습니다",
            )

        time_logs = list(timesheet.get("time_logs", []) or [])
        if time_logs:
            logged_hours = sum(Decimal(str(log.get("hours", 0))) for log in time_logs)
            if logged_hours != total_hours:
                raise_unprocessable(
                    "ERR-PRJ-009",
                    "총 근무시간은 time_logs 합계와 일치해야 합니다",
                )
            TimesheetService._validate_time_logs(
                time_logs,
                start_date=start_date,
                end_date=end_date,
                require_dates=True,
            )
        return total_hours, time_logs

    @staticmethod
    def validate_draft_document(
        *,
        start_date: Any,
        end_date: Any,
        time_logs: list[dict[str, Any]],
    ) -> None:
        """초안 저장 시 기간과 선택적 로그 일자를 검증한다."""
        normalized_start, normalized_end = TimesheetService.validate_date_range(
            start_date, end_date
        )
        if time_logs:
            TimesheetService._validate_time_logs(
                time_logs,
                start_date=normalized_start,
                end_date=normalized_end,
                require_dates=False,
            )

    @staticmethod
    def summarize_time_logs(timesheet: dict[str, Any]) -> dict[str, Any]:
        """리스트/상세 응답용 시간 로그 요약을 계산한다."""
        project_refs: set[str] = set()
        task_refs: set[str] = set()
        activity_hours: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
        work_dates: list[DateType] = []
        for log in list(timesheet.get("time_logs", []) or []):
            project_ref = str(log.get("project_ref", "")).strip()
            task_ref = str(log.get("task_ref", "")).strip()
            activity_type = str(log.get("activity_type", "")).strip() or "미분류"
            hours = Decimal(str(log.get("hours", 0)))
            if project_ref:
                project_refs.add(project_ref)
            if task_ref:
                task_refs.add(task_ref)
            if hours > 0:
                activity_hours[activity_type] += hours
            work_date = TimesheetService._coerce_date(log.get("date"))
            if work_date:
                work_dates.append(work_date)

        activity_breakdown = [
            {"activity_type": activity_type, "hours": float(hours)}
            for activity_type, hours in sorted(activity_hours.items())
        ]
        summary: dict[str, Any] = {
            "log_count": len(list(timesheet.get("time_logs", []) or [])),
            "project_refs": sorted(project_refs),
            "task_refs": sorted(task_refs),
            "activity_breakdown": activity_breakdown,
        }
        if work_dates:
            summary["work_date_span"] = {
                "start_date": min(work_dates).isoformat(),
                "end_date": max(work_dates).isoformat(),
            }
        else:
            summary["work_date_span"] = None
        return summary

    @staticmethod
    def apply_task_actual_time_rollup(
        task_repo: Repository, time_logs: list[dict[str, Any]]
    ) -> None:
        """타임시트 로그를 기반으로 작업 실제 시간을 누적 반영한다."""
        increments: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
        for log in time_logs:
            task_ref = str(log.get("task_ref", "")).strip()
            if not task_ref:
                continue
            increments[task_ref] += Decimal(str(log.get("hours", 0)))

        for task_ref, added_hours in increments.items():
            task = task_repo.find_by_id(task_ref)
            if not task:
                continue
            current_actual = Decimal(str(task.get("actual_time", 0)))
            task_repo.update_by_id(task_ref, {"actual_time": current_actual + added_hours})

    @staticmethod
    def build_submission_event_data(
        timesheet: dict[str, Any], total_hours: Decimal
    ) -> dict[str, Any]:
        """Outbox 적재용 이벤트 페이로드를 구성한다."""
        summary = TimesheetService.summarize_time_logs(timesheet)
        time_logs = [
            {
                "date": TimesheetService._coerce_date(log.get("date")).isoformat()
                if TimesheetService._coerce_date(log.get("date"))
                else "",
                "project_ref": log.get("project_ref", ""),
                "task_ref": log.get("task_ref", ""),
                "hours": float(Decimal(str(log.get("hours", 0)))),
                "activity_type": log.get("activity_type", ""),
            }
            for log in list(timesheet.get("time_logs", []) or [])
        ]
        return {
            "employee_id": timesheet.get("employee_id", ""),
            "employee_name": timesheet.get("employee_name", ""),
            "start_date": TimesheetService._coerce_date(timesheet.get("start_date")).isoformat()
            if TimesheetService._coerce_date(timesheet.get("start_date"))
            else "",
            "end_date": TimesheetService._coerce_date(timesheet.get("end_date")).isoformat()
            if TimesheetService._coerce_date(timesheet.get("end_date"))
            else "",
            "total_hours": float(total_hours),
            "payroll_ready_hours": float(total_hours),
            "project_refs": summary["project_refs"],
            "activity_hours": summary["activity_breakdown"],
            "time_logs": time_logs,
        }

    def submit_timesheet(self, timesheet_id: str, *, triggered_by: str = "") -> dict[str, Any]:
        """타임시트를 제출한다."""
        ts = self._ts_repo.find_by_id(timesheet_id)
        if not ts:
            raise_not_found(f"타임시트 '{timesheet_id}'을 찾을 수 없습니다")
        ts = cast("dict[str, Any]", ts)

        total_hours, time_logs = self.validate_submission_document(ts)
        self.apply_task_actual_time_rollup(self._task_repo, time_logs)
        event_data = self.build_submission_event_data(ts, total_hours)
        self._ts_repo.submit_with_event(
            timesheet_id,
            event_type=EventType.TIMESHEET_SUBMITTED,
            event_data=event_data,
            triggered_by=triggered_by,
        )

        logger.info("타임시트 제출: %s (%s시간)", timesheet_id, total_hours)
        return {
            "timesheet_id": timesheet_id,
            "total_hours": total_hours,
            "status": "submitted",
        }

    def generate_invoice_from_timesheet(
        self,
        timesheet_id: str,
        hourly_rate: Decimal | None = None,
    ) -> dict[str, Any]:
        """타임시트 기반 청구서를 생성한다.

        hourly_rate가 없으면 활동유형 billing_rate를 자동 적용한다.
        """
        ts = self._ts_repo.find_by_id(timesheet_id)
        if not ts:
            raise_not_found(f"타임시트 '{timesheet_id}'을 찾을 수 없습니다")
        ts = cast("dict[str, Any]", ts)

        total_hours = Decimal(str(ts.get("total_hours", 0)))
        line_items: list[dict[str, Any]] = []
        rate_source = "hourly_rate"

        if hourly_rate is not None:
            amount = total_hours * hourly_rate
        else:
            time_logs = list(ts.get("time_logs", []) or [])
            if not time_logs:
                raise_unprocessable(
                    "ERR-PRJ-011",
                    "활동유형 단가 청구를 위해 최소 한 건 이상의 time_logs가 필요합니다",
                )

            rate_source = "activity_type"
            hours_by_activity: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
            for log in time_logs:
                activity_type_name = str(log.get("activity_type", "")).strip()
                if not activity_type_name:
                    raise_unprocessable(
                        "ERR-PRJ-012",
                        "모든 time_logs에 활동유형이 있어야 활동 단가를 자동 적용할 수 있습니다",
                    )
                hours_by_activity[activity_type_name] += Decimal(str(log.get("hours", 0)))

            amount = Decimal(0)
            for activity_type_name, hours in hours_by_activity.items():
                matches = self._activity_type_repo.find_many(
                    query={"activity_type": activity_type_name, "is_active": True},
                    limit=1,
                )
                activity_type_doc = matches[0] if matches else None
                if not activity_type_doc:
                    raise_unprocessable(
                        "ERR-PRJ-013",
                        f"활성 활동유형 '{activity_type_name}'의 청구 단가를 찾을 수 없습니다",
                    )

                rate = Decimal(str(activity_type_doc.get("billing_rate", 0)))
                line_amount = hours * rate
                line_items.append(
                    {
                        "activity_type": activity_type_name,
                        "hours": hours,
                        "rate": rate,
                        "amount": line_amount,
                    }
                )
                amount += line_amount

        billing_id = generate_name("PBL", tenant_id=self._tenant_id)
        billing_document: dict[str, Any] = {
            "_id": billing_id,
            "timesheet_ref": timesheet_id,
            "employee_id": ts.get("employee_id", ""),
            "total_hours": total_hours,
            "total": amount,
            "status": "draft",
            "tenant_id": self._tenant_id,
            "rate_source": rate_source,
        }
        if hourly_rate is not None:
            billing_document["hourly_rate"] = hourly_rate
        if line_items:
            billing_document["line_items"] = line_items
        self._billing_repo.insert(billing_document)

        # 타임시트에 청구 완료 표시
        self._ts_repo.update_by_id(timesheet_id, {"billed": True})

        logger.info("타임시트 청구: %s (%s원)", timesheet_id, amount)
        return {
            "billing_id": billing_id,
            "timesheet_id": timesheet_id,
            "total_hours": total_hours,
            "hourly_rate": hourly_rate,
            "amount": amount,
            "rate_source": rate_source,
            "line_item_count": len(line_items),
        }

    def auto_invoice_timesheets(
        self,
        period: str,
        hourly_rate: Decimal | None = None,
    ) -> list[dict[str, Any]]:
        """미청구 타임시트를 일괄 인보이싱한다.

        Args:
            period: 청구 기간 (예: "2026-03")
            hourly_rate: 시간당 단가

        Returns:
            생성된 청구 목록
        """
        # 제출 완료(docstatus=1)이고 미청구인 타임시트 조회
        timesheets = self._ts_repo.find_many(
            {"docstatus": 1, "billed": {"$ne": True}},
            limit=10000,
        )

        results: list[dict[str, Any]] = []
        for ts in timesheets:
            ts_id = ts["_id"]
            result = self.generate_invoice_from_timesheet(ts_id, hourly_rate)
            results.append(result)

        logger.info("일괄 인보이싱 완료: %s — %d건", period, len(results))
        return results
