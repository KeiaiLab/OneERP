"""교대 배정 서비스 — 교대 배정 및 출석 연동 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-012: 교대 배정 기간 검증 (start_date <= end_date)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ShiftService:
    """교대 배정 ↔ 출석 연동 비즈니스 로직.

    교대 배정 조회 및 출석 기록과의 교차 검증을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._shift_repo = Repository("shift_assignments", tenant_id=tenant_id)
        self._attendance_repo = Repository("attendances", tenant_id=tenant_id)

    def get_employee_shift(
        self,
        employee: str,
        target_date: Any,
    ) -> dict[str, Any] | None:
        """특정 날짜의 직원 교대 배정을 조회한다."""
        shifts = self._shift_repo.find_many(
            {
                "employee": employee,
                "start_date": {"$lte": target_date},
                "end_date": {"$gte": target_date},
            },
            limit=1,
        )
        return shifts[0] if shifts else None

    def check_attendance_compliance(
        self,
        employee: str,
        from_date: Any,
        to_date: Any,
    ) -> dict[str, Any]:
        """교대 배정 대비 출석 준수율을 확인한다.

        Args:
            employee: 직원 ID
            from_date: 조회 시작일
            to_date: 조회 종료일

        Returns:
            준수율 정보 (shift_days, attended_days, compliance_rate)
        """
        shifts = self._shift_repo.find_many(
            {
                "employee": employee,
                "start_date": {"$lte": to_date},
                "end_date": {"$gte": from_date},
            },
            limit=1000,
        )

        attendances = self._attendance_repo.find_many(
            {
                "employee": employee,
                "attendance_date": {"$gte": from_date, "$lte": to_date},
                "status": "present",
            },
            limit=1000,
        )

        shift_days = len(shifts)
        attended_days = len(attendances)
        compliance_rate = round(attended_days / shift_days * 100, 1) if shift_days > 0 else 0.0

        return {
            "employee": employee,
            "shift_days": shift_days,
            "attended_days": attended_days,
            "compliance_rate": compliance_rate,
            "absent_days": max(shift_days - attended_days, 0),
        }
