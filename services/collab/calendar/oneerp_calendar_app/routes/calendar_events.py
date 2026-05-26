"""캘린더 이벤트(CalendarEvent) API 라우터."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_calendar_app.models.calendar_event import (
    CalendarEvent,
    CalendarEventCreate,
    CalendarEventUpdate,
)
from oneerp_calendar_app.services.event_service import EventService

router = APIRouter(prefix="/api/v1/calendar-events", tags=["캘린더 이벤트"])

_COLLECTION = "calendar_events"
_PREFIX = "CEVT"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("calendar_event:create"))]
)
def 이벤트_생성(body: CalendarEventCreate, user: CurrentUserDep) -> dict[str, Any]:
    """캘린더 이벤트를 생성한다.

    BR-CAL-010: 캘린더 존재 확인.
    BR-CAL-011: 날짜 유효성 검증.
    """
    svc = EventService(user.tenant_id)
    svc.check_calendar_exists(body.calendar_id)

    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    doc = CalendarEvent(
        _id=doc_id,
        tenant_id=user.tenant_id,
        calendar_id=body.calendar_id,
        title=body.title,
        description=body.description,
        event_type=body.event_type,
        start_dt=body.start_dt,
        end_dt=body.end_dt,
        all_day=body.all_day,
        location=body.location,
        organizer_id=body.organizer_id or user.sub,
        recurrence_frequency=body.recurrence_frequency,
        recurrence_interval=body.recurrence_interval,
        recurrence_end_date=body.recurrence_end_date,
        recurrence_count=body.recurrence_count,
        ref_doctype=body.ref_doctype,
        ref_docname=body.ref_docname,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {"id": doc_id, "message": "이벤트가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("calendar_event:read"))])
def 이벤트_목록(
    user: CurrentUserDep,
    calendar_id: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """캘린더 이벤트 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if calendar_id:
        query["calendar_id"] = calendar_id
    skip = (page - 1) * page_size
    docs = repo.find_many(query, skip=skip, limit=page_size, sort=[("start_dt", -1)])
    total_count = repo.count(query)
    return {"data": docs, "total": total_count, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("calendar_event:read"))])
def 이벤트_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """이벤트 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이벤트를 찾을 수 없습니다")
    assert doc is not None
    return doc


@router.patch("/{doc_id}", dependencies=[Depends(require_permission("calendar_event:write"))])
def 이벤트_수정(doc_id: str, body: CalendarEventUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """이벤트를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이벤트를 찾을 수 없습니다")
    updates = body.model_dump(exclude_none=True)
    updates["updated_by"] = user.sub
    repo.update_by_id(doc_id, updates)
    return {"id": doc_id, "message": "이벤트가 수정되었습니다"}


@router.post(
    "/{doc_id}/confirm",
    dependencies=[Depends(require_permission("calendar_event:write"))],
)
def 이벤트_확정(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BR-CAL-014: 이벤트를 확정한다."""
    svc = EventService(user.tenant_id)
    return svc.change_event_status(doc_id, "confirmed")


@router.post(
    "/{doc_id}/cancel",
    dependencies=[Depends(require_permission("calendar_event:write"))],
)
def 이벤트_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BR-CAL-014: 이벤트를 취소한다."""
    svc = EventService(user.tenant_id)
    return svc.change_event_status(doc_id, "cancelled")


@router.post(
    "/{doc_id}/invitees",
    status_code=201,
    dependencies=[Depends(require_permission("calendar_event:write"))],
)
def 초대자_추가(
    doc_id: str,
    user: CurrentUserDep,
    user_id: str = "",
    user_name: str = "",
    email: str = "",
) -> dict[str, Any]:
    """BR-CAL-021: 이벤트에 초대자를 추가한다."""
    if not user_id:
        raise_bad_request("user_id는 필수입니다")
    svc = EventService(user.tenant_id)
    return svc.add_invitee(doc_id, user_id, user_name, email)


@router.post(
    "/{doc_id}/respond",
    dependencies=[Depends(require_permission("calendar_event:write"))],
)
def 초대_응답(
    doc_id: str,
    user: CurrentUserDep,
    response_status: str = "",
    response_comment: str = "",
) -> dict[str, Any]:
    """BR-CAL-022: 초대에 응답한다."""
    if not response_status:
        raise_bad_request("response_status는 필수입니다")
    svc = EventService(user.tenant_id)
    return svc.respond_to_invite(doc_id, user.sub, response_status, response_comment)


@router.get(
    "/{doc_id}/conflicts",
    dependencies=[Depends(require_permission("calendar_event:read"))],
)
def 충돌_검사(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BR-CAL-015: 이벤트의 시간 충돌을 검사한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이벤트를 찾을 수 없습니다")
    assert doc is not None

    start_dt = doc.get("start_dt")
    end_dt = doc.get("end_dt")
    organizer = doc.get("organizer_id", "")
    if not start_dt or not end_dt or not organizer:
        return {"conflicts": []}

    if isinstance(start_dt, str):
        start_dt = datetime.fromisoformat(start_dt)
    if isinstance(end_dt, str):
        end_dt = datetime.fromisoformat(end_dt)

    svc = EventService(user.tenant_id)
    conflicts = svc.detect_conflicts(
        organizer,
        start_dt,
        end_dt,
        exclude_event_id=doc_id,
    )
    return {"conflicts": conflicts, "count": len(conflicts)}


@router.post(
    "/{doc_id}/generate-recurrence",
    dependencies=[Depends(require_permission("calendar_event:create"))],
)
def 반복_이벤트_생성(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BR-CAL-013: 반복 이벤트 인스턴스를 생성한다."""
    svc = EventService(user.tenant_id)
    generated = svc.generate_recurring_events(doc_id)
    return {"generated": generated, "count": len(generated)}
