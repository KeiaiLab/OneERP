"""급여대장(PayrollEntry) CRUD + submit/cancel 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.payroll_entry import PayrollEntry, PayrollEntryCreate, PayrollEntryUpdate

router = APIRouter(prefix="/api/v1/payroll-entries", tags=["급여대장"])
_COLLECTION = "payroll_entries"
_PREFIX = "PRLE"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("payroll_entry:create"))]
)
async def create_payroll_entry(body: PayrollEntryCreate) -> dict:
    """급여대장을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = PayrollEntry(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"id": doc_id, "message": "급여대장이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("payroll_entry:read"))])
async def list_payroll_entries(page: int = 1, page_size: int = 20) -> dict:
    """급여대장 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("payroll_entry:read"))])
async def get_payroll_entry(doc_id: str) -> dict:
    """급여대장 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여대장을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("payroll_entry:write"))])
async def update_payroll_entry(doc_id: str, body: PayrollEntryUpdate) -> dict:
    """급여대장을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여대장을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "급여대장이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("payroll_entry:delete"))])
async def delete_payroll_entry(doc_id: str) -> dict:
    """급여대장을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여대장을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "급여대장이 삭제되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("payroll_entry:submit"))])
async def submit_payroll_entry(doc_id: str, user: CurrentUserDep) -> dict:
    """급여대장을 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여대장을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="초안 상태에서만 제출 가능",
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.PAYROLL_ENTRY_SUBMITTED,
        event_data={
            "doc_id": doc_id,
            "total_gross": doc.get("total_gross", 0),
            "total_net": doc.get("total_net", 0),
            "employee_count": doc.get("employee_count", 0),
            "posting_date": str(doc.get("posting_date", "")),
        },
        triggered_by=user.sub,
    )
    return {"message": "급여대장이 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("payroll_entry:cancel"))])
async def cancel_payroll_entry(doc_id: str) -> dict:
    """급여대장을 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여대장을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="제출된 문서만 취소 가능",
        )
    repo.cancel(doc_id)
    return {"message": "급여대장이 취소되었습니다"}
