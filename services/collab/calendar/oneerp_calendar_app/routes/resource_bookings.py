"""자원 예약(ResourceBooking) API 라우터."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.permissions import require_permission

from oneerp_calendar_app.models.resource_booking import ResourceBookingCreate
from oneerp_calendar_app.services.resource_booking_service import ResourceBookingService

router = APIRouter(prefix="/api/v1/resource-bookings", tags=["자원 예약"])


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("resource_booking:create"))],
)
def 자원예약_생성(body: ResourceBookingCreate, user: CurrentUserDep) -> dict[str, Any]:
    """BR-CAL-050: 자원을 예약한다."""
    svc = ResourceBookingService(user.tenant_id)
    return svc.book_resource(
        event_id=body.event_id,
        resource_id=body.resource_id,
        start_dt=body.start_dt,
        end_dt=body.end_dt,
        booked_by=body.booked_by or user.sub,
    )


@router.get("", dependencies=[Depends(require_permission("resource_booking:read"))])
def 자원예약_목록(
    user: CurrentUserDep,
    resource_id: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """자원 예약 목록을 조회한다."""
    svc = ResourceBookingService(user.tenant_id)
    return svc.list_bookings(resource_id=resource_id, page=page, page_size=page_size)


@router.post(
    "/{booking_id}/cancel",
    dependencies=[Depends(require_permission("resource_booking:write"))],
)
def 자원예약_취소(booking_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자원 예약을 취소한다."""
    svc = ResourceBookingService(user.tenant_id)
    return svc.cancel_booking(booking_id)


@router.get(
    "/availability",
    dependencies=[Depends(require_permission("resource_booking:read"))],
)
def 자원_가용성_조회(
    resource_id: str,
    start_dt: str,
    end_dt: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """자원의 가용 시간대를 조회한다."""
    if not resource_id:
        raise_bad_request("resource_id는 필수입니다")

    try:
        s = datetime.fromisoformat(start_dt)
        e = datetime.fromisoformat(end_dt)
    except ValueError:
        raise_bad_request("유효하지 않은 날짜 형식입니다")
        return {}

    svc = ResourceBookingService(user.tenant_id)
    return svc.get_resource_availability(resource_id, s, e)
