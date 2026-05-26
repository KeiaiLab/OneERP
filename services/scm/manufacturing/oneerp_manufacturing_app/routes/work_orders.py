"""작업지시(WorkOrder) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_manufacturing_app.models.work_order import (
    WorkOrder,
    WorkOrderCreate,
    WorkOrderStatus,
    WorkOrderUpdate,
)

router = APIRouter(prefix="/api/v1/work-orders", tags=["작업지시"])

_COLLECTION = "work_orders"
_PREFIX = "WO"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("work_order:create"))])
def create_work_order(body: WorkOrderCreate, user: CurrentUserDep) -> dict[str, Any]:
    """작업지시를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    wo = WorkOrder(
        _id=doc_id,
        tenant_id=user.tenant_id,
        production_item=body.production_item,
        bom_ref=body.bom_ref,
        qty=body.qty,
        planned_start_date=body.planned_start_date,
        planned_end_date=body.planned_end_date,
        warehouse=body.warehouse,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(wo)
    return {"id": doc_id, "message": "작업지시가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("work_order:read"))])
def list_work_orders(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """작업지시 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("work_order:read"))])
def get_work_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """작업지시 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업지시를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("work_order:write"))])
def update_work_order(
    doc_id: str,
    body: WorkOrderUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """작업지시를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업지시를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "작업지시가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("work_order:submit"))])
def submit_work_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """작업지시를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업지시를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.update_by_id(doc_id, {"status": WorkOrderStatus.NOT_STARTED, "updated_by": user.sub})
    repo.submit_with_event(
        doc_id,
        event_type=EventType.WORK_ORDER_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "작업지시가 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("work_order:cancel"))])
def cancel_work_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """작업지시를 취소한다 (제출 → 취소)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업지시를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.update_by_id(doc_id, {"status": WorkOrderStatus.CANCELLED, "updated_by": user.sub})
    repo.cancel(doc_id)
    return {"id": doc_id, "message": "작업지시가 취소되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("work_order:delete"))]
)
def delete_work_order(doc_id: str, user: CurrentUserDep) -> None:
    """작업지시를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업지시를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    repo.delete_by_id(doc_id)
