"""공휴일(Holiday) API 라우터."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.permissions import require_permission

from oneerp_calendar_app.services.holiday_service import HolidayService

router = APIRouter(prefix="/api/v1/holidays", tags=["공휴일"])

_COLLECTION = "holidays"


@router.get(
    "/business-days",
    dependencies=[Depends(require_permission("holiday:read"))],
)
def 근무일_계산(
    start_date: str,
    end_date: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """BR-CAL-063: 두 날짜 사이의 근무일 수를 계산한다."""
    try:
        s = date.fromisoformat(start_date)
        e = date.fromisoformat(end_date)
    except ValueError:
        raise_bad_request("유효하지 않은 날짜 형식입니다")

    svc = HolidayService(user.tenant_id)
    return svc.calculate_business_days(s, e)


@router.get(
    "/check",
    dependencies=[Depends(require_permission("holiday:read"))],
)
def 공휴일_확인(
    check_date: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """특정 날짜가 공휴일인지 확인한다."""
    try:
        d = date.fromisoformat(check_date)
    except ValueError:
        raise_bad_request("유효하지 않은 날짜 형식입니다")

    svc = HolidayService(user.tenant_id)
    return {"date": check_date, "is_holiday": svc.is_holiday(d)}


@router.get(
    "/range",
    dependencies=[Depends(require_permission("holiday:read"))],
)
def 기간별_공휴일_조회(
    start_date: str,
    end_date: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """기간 내 공휴일 목록을 반환한다."""
    try:
        s = date.fromisoformat(start_date)
        e = date.fromisoformat(end_date)
    except ValueError:
        raise_bad_request("유효하지 않은 날짜 형식입니다")

    svc = HolidayService(user.tenant_id)
    holidays = svc.get_holidays_in_range(s, e)
    return {"holidays": holidays, "count": len(holidays)}
