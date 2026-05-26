"""급여세신고(PayrollTaxReturn) CRUD + submit/cancel 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.payroll_tax_return import (
    PayrollTaxReturn,
    PayrollTaxReturnCreate,
    PayrollTaxReturnUpdate,
)

router = APIRouter(prefix="/api/v1/payroll-tax-returns", tags=["급여세신고"])
_COLLECTION = "payroll_tax_returns"
_PREFIX = "PTR"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("payroll_tax_return:create"))]
)
async def create_payroll_tax_return(body: PayrollTaxReturnCreate) -> dict:
    """급여세신고를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = PayrollTaxReturn(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"payroll_tax_return_id": doc_id, "message": "급여세신고가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("payroll_tax_return:read"))])
async def list_payroll_tax_returns(page: int = 1, page_size: int = 20) -> dict:
    """급여세신고 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("payroll_tax_return:read"))])
async def get_payroll_tax_return(doc_id: str) -> dict:
    """급여세신고 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="급여세신고를 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("payroll_tax_return:write"))])
async def update_payroll_tax_return(doc_id: str, body: PayrollTaxReturnUpdate) -> dict:
    """급여세신고를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="급여세신고를 찾을 수 없습니다"
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "급여세신고가 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("payroll_tax_return:submit"))]
)
async def submit_payroll_tax_return(doc_id: str, user: CurrentUserDep) -> dict:
    """급여세신고를 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="급여세신고를 찾을 수 없습니다"
        )
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="초안 상태에서만 제출 가능",
        )
    repo.submit_with_event(
        doc_id, event_type=EventType.PAYROLL_TAX_RETURN_SUBMITTED, triggered_by=user.sub
    )
    return {"message": "급여세신고가 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("payroll_tax_return:cancel"))]
)
async def cancel_payroll_tax_return(doc_id: str) -> dict:
    """급여세신고를 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="급여세신고를 찾을 수 없습니다"
        )
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="제출된 문서만 취소 가능",
        )
    repo.cancel(doc_id)
    return {"message": "급여세신고가 취소되었습니다"}
