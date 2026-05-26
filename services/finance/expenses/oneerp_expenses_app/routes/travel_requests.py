"""출장신청(TravelRequest) CRUD + submit/cancel/settle 라우트."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from ..models.travel_request import (
    TravelRequest,
    TravelRequestCreate,
    TravelRequestUpdate,
)
from ..services.expense_route_service import ExpenseRouteService
from ..services.expense_service import ExpenseService

router = APIRouter(prefix="/api/v1/travel-requests", tags=["출장신청"])
_COLLECTION = "travel_requests"
_PREFIX = "TR"


def _get_service(tenant_id: str) -> ExpenseRouteService:
    """요청 테넌트에 바인딩된 route service를 반환한다."""
    return ExpenseRouteService(_COLLECTION, tenant_id)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("travel_request:create"))]
)
async def create_travel_request(body: TravelRequestCreate, user: CurrentUserDep) -> dict:
    """출장신청을 생성한다."""
    service = _get_service(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = TravelRequest(_id=doc_id, **body.model_dump())
    service.create(doc)
    return {"travel_request_id": doc_id, "message": "출장신청이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("travel_request:read"))])
async def list_travel_requests(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """출장신청 목록을 페이지네이션으로 조회한다."""
    service = _get_service(user.tenant_id)
    return service.list_page(page=page, page_size=page_size)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("travel_request:read"))])
async def get_travel_request(doc_id: str, user: CurrentUserDep) -> dict:
    """출장신청 상세 정보를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_or_raise(doc_id, detail="출장신청을 찾을 수 없습니다")


@router.put("/{doc_id}", dependencies=[Depends(require_permission("travel_request:write"))])
async def update_travel_request(
    doc_id: str, body: TravelRequestUpdate, user: CurrentUserDep
) -> dict:
    """출장신청을 수정한다."""
    service = _get_service(user.tenant_id)
    service.get_or_raise(doc_id, detail="출장신청을 찾을 수 없습니다")
    service.update(doc_id, body.model_dump(exclude_none=True))
    return {"message": "출장신청이 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("travel_request:submit"))]
)
async def submit_travel_request(doc_id: str, user: CurrentUserDep) -> dict:
    """출장신청을 제출한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_or_raise(doc_id, detail="출장신청을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="초안 상태에서만 제출 가능",
        )
    service.submit(doc_id, event_type=EventType.TRAVEL_REQUEST_SUBMITTED, triggered_by=user.sub)
    return {"message": "출장신청이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("travel_request:cancel"))]
)
async def cancel_travel_request(doc_id: str, user: CurrentUserDep) -> dict:
    """출장신청을 취소한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_or_raise(doc_id, detail="출장신청을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="제출된 문서만 취소 가능",
        )
    service.cancel(doc_id)
    return {"message": "출장신청이 취소되었습니다"}


class _ActualExpenseItem(BaseModel):
    """출장 정산 실제 경비 항목."""

    expense_type: str
    amount: float
    description: str = ""


class _SettleTravelBody(BaseModel):
    """출장 정산 요청 바디."""

    actual_expenses: list[_ActualExpenseItem]


@router.post(
    "/{doc_id}/settle",
    dependencies=[Depends(require_permission("travel_request:write"))],
)
async def settle_travel_request(
    doc_id: str,
    body: _SettleTravelBody,
    user: CurrentUser = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """출장 경비를 정산한다 (BR-EXP-004)."""
    service = ExpenseService(tenant_id=user.tenant_id)
    return service.settle_travel(
        doc_id,
        [item.model_dump() for item in body.actual_expenses],
    )
