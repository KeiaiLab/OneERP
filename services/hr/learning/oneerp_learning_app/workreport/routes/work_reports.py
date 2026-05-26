"""업무일지(WorkReport) CRUD + submit/approve/reject/cancel 라우트."""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.work_report import (
    WorkReport,
    WorkReportCreate,
    WorkReportStatus,
    WorkReportUpdate,
)
from ..services.work_report_service import WorkReportService

router = APIRouter(prefix="/api/v1/work-reports", tags=["업무일지"])
_COLLECTION = "work_reports"
_PREFIX = "WR"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


def _get_service(tenant_id: str = "default") -> WorkReportService:
    """WorkReportService 인스턴스를 반환한다."""
    return WorkReportService(tenant_id=tenant_id)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("work_report:create"))],
)
async def create_work_report(body: WorkReportCreate, user: CurrentUserDep) -> dict:
    """업무일지를 생성한다.

    BR-WR-002: 보고일자 미래일 불가 (모델 validator에서 검증).
    """
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)

    body_data = body.model_dump()
    service = _get_service()

    # 항목이 있으면 총 작업시간 자동 계산
    items = body_data.get("items", [])
    total_hours = service.calculate_total_hours(items)

    doc = WorkReport(
        _id=doc_id,
        total_hours=total_hours,
        created_by=user.sub,
        **body_data,
    )
    repo.insert(doc)

    return {"id": doc_id, "message": "업무일지가 생성되었습니다"}


@router.get(
    "/",
    dependencies=[Depends(require_permission("work_report:read"))],
)
async def list_work_reports(
    page: int = 1,
    page_size: int = 20,
    employee_id: str | None = None,
    status: WorkReportStatus | None = None,
) -> dict:
    """업무일지 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    query: dict = {}
    if employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    data = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count(query)
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}",
    dependencies=[Depends(require_permission("work_report:read"))],
)
async def get_work_report(doc_id: str) -> dict:
    """업무일지 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="ERR-WR-001", detail="업무일지를 찾을 수 없습니다")
    return doc


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("work_report:write"))],
)
async def update_work_report(doc_id: str, body: WorkReportUpdate, user: CurrentUserDep) -> dict:
    """업무일지를 수정한다.

    BR-WR-001: 작성자 본인만 수정 가능.
    BR-WR-005: 제출 후 수정 불가.
    """
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="ERR-WR-001", detail="업무일지를 찾을 수 없습니다")

    # BR-WR-001: 작성자 본인 확인
    if doc.get("employee_id", "") != user.sub and doc.get("created_by", "") != user.sub:
        raise OneERPError(
            status_code=403,
            error="ERR-WR-010",
            detail="작성자 본인만 수정할 수 있습니다 (BR-WR-001)",
        )

    # BR-WR-005: 제출 후 수정 불가
    current_status = doc.get("status", WorkReportStatus.DRAFT)
    if current_status not in (WorkReportStatus.DRAFT, WorkReportStatus.REJECTED):
        raise OneERPError(
            status_code=400,
            error="ERR-WR-005",
            detail=f"현재 상태({current_status})에서는 수정할 수 없습니다 (BR-WR-005)",
        )

    update_data = body.model_dump(exclude_none=True)

    # 항목이 변경되면 총 작업시간 재계산
    if "items" in update_data:
        service = _get_service()
        update_data["total_hours"] = service.calculate_total_hours(update_data["items"])

    repo.update_by_id(doc_id, update_data)
    return {"message": "업무일지가 수정되었습니다"}


@router.post(
    "/{doc_id}/submit",
    dependencies=[Depends(require_permission("work_report:submit"))],
)
async def submit_work_report(doc_id: str, user: CurrentUserDep) -> dict:
    """업무일지를 제출한다.

    BR-WR-001, BR-WR-003, BR-WR-004, BR-WR-005.
    """
    service = _get_service()
    result = service.submit_report(doc_id, submitted_by=user.sub)
    return {"message": "업무일지가 제출되었습니다", **result}


@router.post(
    "/{doc_id}/approve",
    dependencies=[Depends(require_permission("work_report:approve"))],
)
async def approve_work_report(doc_id: str, user: CurrentUserDep, comment: str = "") -> dict:
    """업무일지를 승인한다.

    BR-WR-006, BR-WR-007.
    """
    service = _get_service()
    result = service.approve_report(doc_id, reviewer_id=user.sub, comment=comment)
    return {"message": "업무일지가 승인되었습니다", **result}


@router.post(
    "/{doc_id}/reject",
    dependencies=[Depends(require_permission("work_report:reject"))],
)
async def reject_work_report(doc_id: str, user: CurrentUserDep, reason: str = "") -> dict:
    """업무일지를 반려한다.

    BR-WR-006, BR-WR-008.
    """
    service = _get_service()
    result = service.reject_report(doc_id, reviewer_id=user.sub, reason=reason)
    return {"message": "업무일지가 반려되었습니다", **result}


@router.post(
    "/{doc_id}/cancel",
    dependencies=[Depends(require_permission("work_report:cancel"))],
)
async def cancel_work_report(doc_id: str, user: CurrentUserDep) -> dict:
    """업무일지를 취소한다.

    BR-WR-001, BR-WR-009.
    """
    service = _get_service()
    result = service.cancel_report(doc_id, cancelled_by=user.sub)
    return {"message": "업무일지가 취소되었습니다", **result}


@router.get(
    "/statistics/{employee_id}",
    dependencies=[Depends(require_permission("work_report:read"))],
)
async def get_employee_statistics(
    employee_id: str,
    start_date: date,
    end_date: date,
) -> dict:
    """직원의 업무일지 통계를 조회한다."""
    service = _get_service()
    return service.get_employee_statistics(employee_id, start_date, end_date)


@router.post(
    "/from-template/{template_id}",
    status_code=201,
    dependencies=[Depends(require_permission("work_report:create"))],
)
async def create_from_template(
    template_id: str,
    user: CurrentUserDep,
    report_date: date | None = None,
) -> dict:
    """템플릿에서 업무일지를 생성한다."""
    service = _get_service()
    rd = report_date or datetime.now(tz=UTC).date()
    result = service.create_from_template(
        template_id=template_id,
        employee_id=user.sub,
        employee_name="",
        report_date=rd,
    )
    return {"message": "템플릿 기반 업무일지가 생성되었습니다", **result}
