"""경비청구(ExpenseClaim) CRUD + submit/cancel 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_bad_request
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from ..models.expense_claim import ExpenseClaim, ExpenseClaimCreate, ExpenseClaimUpdate
from ..services.expense_route_service import ExpenseRouteService

router = APIRouter(prefix="/api/v1/expense-claims", tags=["경비청구"])
_COLLECTION = "expense_claims"
_PREFIX = "EXP"


def _get_service(tenant_id: str) -> ExpenseRouteService:
    """요청 테넌트에 바인딩된 route service를 반환한다."""
    return ExpenseRouteService(_COLLECTION, tenant_id)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("expense_claim:create"))]
)
async def create_expense_claim(body: ExpenseClaimCreate, user: CurrentUserDep) -> dict:
    """경비청구를 생성한다."""
    service = _get_service(user.tenant_id)
    doc_id = generate_name(_PREFIX)

    # total_claimed_amount가 지정되었으면 total_amount에도 동기화
    body_data = body.model_dump()
    if body_data.get("total_claimed_amount", 0) > 0 and body_data.get("total_amount", 0) == 0:
        body_data["total_amount"] = body_data["total_claimed_amount"]
    elif body_data.get("total_amount", 0) > 0 and body_data.get("total_claimed_amount", 0) == 0:
        body_data["total_claimed_amount"] = body_data["total_amount"]

    doc = ExpenseClaim(_id=doc_id, **body_data)
    service.create(doc)
    return {"id": doc_id, "message": "경비청구가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("expense_claim:read"))])
async def list_expense_claims(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """경비청구 목록을 페이지네이션으로 조회한다."""
    service = _get_service(user.tenant_id)
    return service.list_page(page=page, page_size=page_size)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("expense_claim:read"))])
async def get_expense_claim(doc_id: str, user: CurrentUserDep) -> dict:
    """경비청구 상세 정보를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_or_raise(doc_id, detail="경비청구를 찾을 수 없습니다")


@router.put("/{doc_id}", dependencies=[Depends(require_permission("expense_claim:write"))])
async def update_expense_claim(doc_id: str, body: ExpenseClaimUpdate, user: CurrentUserDep) -> dict:
    """경비청구를 수정한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_or_raise(doc_id, detail="경비청구를 찾을 수 없습니다")
    # BR-EXP-008: 초안 상태에서만 수정 가능
    if doc.get("docstatus", 0) != 0:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")
    service.update(doc_id, body.model_dump(exclude_none=True))
    return {"message": "경비청구가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("expense_claim:submit"))])
async def submit_expense_claim(doc_id: str, user: CurrentUserDep) -> dict:
    """경비청구를 제출한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_or_raise(doc_id, detail="경비청구를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="초안 상태에서만 제출 가능",
        )
    # total_claimed_amount 우선, 없으면 total_amount 사용
    total = doc.get("total_claimed_amount") or doc.get("total_amount", 0)
    service.submit(
        doc_id,
        event_type=EventType.EXPENSE_CLAIM_SUBMITTED,
        event_data={
            "doc_id": doc_id,
            "total_amount": total,
            "total_claimed_amount": total,
            "employee_id": doc.get("employee_id", doc.get("employee", "")),
            "expense_type": doc.get("expense_type", ""),
            "posting_date": str(doc.get("posting_date", "")),
        },
        triggered_by=user.sub,
    )
    return {"message": "경비청구가 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("expense_claim:cancel"))])
async def cancel_expense_claim(doc_id: str, user: CurrentUserDep) -> dict:
    """경비청구를 취소한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_or_raise(doc_id, detail="경비청구를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="제출된 문서만 취소 가능",
        )
    service.cancel(doc_id)
    return {"message": "경비청구가 취소되었습니다"}
