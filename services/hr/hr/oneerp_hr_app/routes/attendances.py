"""근태(Attendance) 커스텀 라우터.

체크인/체크아웃, 근태 워크벤치, 일일 리포트, 주간 52시간 요약을 제공한다.
"""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import delete_draft, get_or_404
from pydantic import BaseModel

from oneerp_hr_app.models.attendance import Attendance, AttendanceCreate, AttendanceUpdate
from oneerp_hr_app.services.attendance_service import (
    AttendanceLocationValidationError,
    AttendanceService,
)

router = APIRouter(prefix="/api/v1/attendances", tags=["출퇴근"])

_COLLECTION = "attendances"
_PREFIX = "ATT"
_NOT_FOUND_MESSAGE = "출퇴근 기록을 찾을 수 없습니다"


class AttendanceCheckInRequest(BaseModel):
    """체크인 요청."""

    employee_id: str
    employee_name: str = ""
    department: str = ""
    attendance_date: date
    shift_name: str = ""
    scheduled_start_time: str = ""
    scheduled_end_time: str = ""
    capture_channel: str = "web"
    ip_address: str = ""
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    recorded_at: datetime
    status: str = "present"


class AttendanceCheckOutRequest(BaseModel):
    """체크아웃 요청."""

    recorded_at: datetime


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _serialize_attendance(document: dict[str, Any]) -> dict[str, Any]:
    return AttendanceService.build_attendance_view(document)


@router.post("", status_code=201, dependencies=[Depends(require_permission("attendance:create"))])
def create_attendance(body: AttendanceCreate, user: CurrentUserDep) -> dict[str, Any]:
    """근태 기록을 수동 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    payload = body.model_dump()
    attendance = Attendance(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(attendance)
    return _serialize_attendance({"_id": doc_id, **payload})


@router.post(
    "/check-in", status_code=201, dependencies=[Depends(require_permission("attendance:create"))]
)
def check_in_attendance(body: AttendanceCheckInRequest, user: CurrentUserDep) -> dict[str, Any]:
    """출근 체크인을 기록한다."""
    repo = _get_repo(user.tenant_id)
    service = AttendanceService(tenant_id=user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    try:
        payload = service.build_check_in_payload(body.model_dump())
    except AttendanceLocationValidationError as exc:
        raise_unprocessable(exc.code, exc.message)

    attendance = Attendance(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(attendance)
    return _serialize_attendance({"_id": doc_id, **payload})


@router.get("/report", dependencies=[Depends(require_permission("attendance:read"))])
def get_attendance_report(
    user: CurrentUserDep,
    attendance_date: date,
    department: str | None = None,
) -> dict[str, Any]:
    """일일 근태 현황과 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {"attendance_date": attendance_date}
    if department:
        query["department"] = department
    records = repo.find_many(query, limit=1000, sort=[("employee_name", 1)])
    summary = AttendanceService.build_daily_report(records)
    return {
        "data": [_serialize_attendance(record) for record in records],
        "total": len(records),
        "attendance_date": attendance_date.isoformat(),
        "department": department or "",
        "summary": summary,
    }


@router.get("/weekly-summary", dependencies=[Depends(require_permission("attendance:read"))])
def get_weekly_attendance_summary(
    user: CurrentUserDep,
    employee_id: str,
    week_start_date: str,
) -> dict[str, Any]:
    """직원별 주간 근무시간과 52시간 초과 여부를 조회한다."""
    service = AttendanceService(tenant_id=user.tenant_id)
    return service.check_weekly_work_hours(employee_id, week_start_date)


@router.get("", dependencies=[Depends(require_permission("attendance:read"))])
def list_attendances(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    employee_id: str | None = None,
    attendance_date: date | None = None,
    department: str | None = None,
    status: str | None = None,
    capture_channel: str | None = None,
    location_status: str | None = None,
) -> dict[str, Any]:
    """근태 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if employee_id:
        query["employee_id"] = employee_id
    if attendance_date:
        query["attendance_date"] = attendance_date
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if capture_channel:
        query["capture_channel"] = capture_channel
    if location_status:
        query["location_status"] = location_status
    skip = (page - 1) * page_size
    documents = repo.find_many(query, skip=skip, limit=page_size, sort=[("attendance_date", -1)])
    return {
        "data": [_serialize_attendance(doc) for doc in documents],
        "total": repo.count(query),
        "page": page,
        "page_size": page_size,
        "summary": AttendanceService.build_workbench_summary(documents),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("attendance:read"))])
def get_attendance(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """근태 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    return _serialize_attendance(doc)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("attendance:write"))])
def update_attendance(
    doc_id: str,
    body: AttendanceUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """근태 기록을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND_MESSAGE)
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _serialize_attendance({**doc, **update_data})


@router.post("/{doc_id}/check-out", dependencies=[Depends(require_permission("attendance:write"))])
def check_out_attendance(
    doc_id: str,
    body: AttendanceCheckOutRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """퇴근 체크아웃을 기록한다."""
    repo = _get_repo(user.tenant_id)
    attendance = get_or_404(repo, doc_id, _NOT_FOUND_MESSAGE)
    service = AttendanceService(tenant_id=user.tenant_id)
    update_data = service.build_check_out_payload(attendance, body.recorded_at)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _serialize_attendance({**attendance, **update_data})


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("attendance:delete"))]
)
def delete_attendance(doc_id: str, user: CurrentUserDep) -> None:
    """초안 상태의 근태 기록만 삭제한다."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND_MESSAGE)
