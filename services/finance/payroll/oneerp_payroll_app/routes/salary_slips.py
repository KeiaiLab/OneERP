"""급여명세(SalarySlip) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import delete_draft, get_or_404, paginated_list, submit_document

from oneerp_payroll_app.models.salary_slip import SalarySlip, SalarySlipCreate

router = APIRouter(prefix="/api/v1/salary-slips", tags=["급여명세"])

_COLLECTION = "salary_slips"
_PREFIX = "SLIP"
_NOT_FOUND = "급여명세를 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("salary_slip:create"))])
def create_salary_slip(
    body: SalarySlipCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """급여명세를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    slip = SalarySlip(
        _id=doc_id,
        tenant_id=user.tenant_id,
        employee_id=body.employee_id,
        employee_name=body.employee_name,
        salary_structure_ref=body.salary_structure_ref,
        payroll_entry_id=body.payroll_entry_id,
        posting_date=body.posting_date,
        start_date=body.start_date,
        end_date=body.end_date,
        gross_pay=body.gross_pay,
        total_deduction=body.total_deduction,
        net_pay=body.net_pay,
        earnings=body.earnings,
        deductions=body.deductions,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(slip)
    return {"id": doc_id, "message": "급여명세가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("salary_slip:read"))])
def list_salary_slips(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    payroll_entry_id: str | None = None,
) -> dict[str, Any]:
    """급여명세 목록을 페이지네이션으로 조회한다.

    필터:
        payroll_entry_id: 급여대장 ID로 필터링
    """
    repo = _get_repo(user.tenant_id)
    filter_query: dict[str, Any] | None = None
    if payroll_entry_id:
        filter_query = {"payroll_entry_id": payroll_entry_id}
    return paginated_list(repo, page, page_size, filter_query=filter_query)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("salary_slip:read"))])
def get_salary_slip(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """급여명세 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return get_or_404(repo, doc_id, _NOT_FOUND)


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("salary_slip:submit"))])
def submit_salary_slip(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """급여명세를 제출한다 (draft -> submitted)."""
    repo = _get_repo(user.tenant_id)
    submit_document(repo, doc_id, _NOT_FOUND)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.SALARY_SLIP_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "급여명세가 제출되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("salary_slip:delete"))]
)
def delete_salary_slip(doc_id: str, user: CurrentUserDep) -> None:
    """급여명세를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)
