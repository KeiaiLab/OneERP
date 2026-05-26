"""생산계획(ProductionPlan) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.production_plan import (
    ProductionPlan,
    ProductionPlanCreate,
    ProductionPlanUpdate,
)
from ..services.work_order_service import WorkOrderService

router = APIRouter(prefix="/api/v1/production-plans", tags=["생산계획"])

_COLLECTION = "production_plans"
_PREFIX = "PP"


def _get_repo() -> Repository:
    """생산계획 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("production_plan:create"))]
)
def create_production_plan(body: ProductionPlanCreate) -> dict:
    """생산계획을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = ProductionPlan(
        planned_start=body.planned_start,
        planned_end=body.planned_end,
        status=body.status,
        items=body.items,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "생산계획이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("production_plan:read"))])
def list_production_plans(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """생산계획 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("production_plan:read"))])
def get_production_plan(doc_id: str) -> dict:
    """생산계획을 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="생산계획을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("production_plan:write"))])
def update_production_plan(doc_id: str, body: ProductionPlanUpdate) -> dict:
    """생산계획을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="생산계획을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "생산계획이 수정되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=200,
    dependencies=[Depends(require_permission("production_plan:delete"))],
)
def delete_production_plan(doc_id: str) -> dict:
    """생산계획을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="생산계획을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "생산계획이 삭제되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("production_plan:submit"))]
)
def submit_production_plan(doc_id: str, user: CurrentUserDep) -> dict:
    """생산계획을 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="생산계획을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.PRODUCTION_PLAN_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"message": "생산계획이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("production_plan:cancel"))]
)
def cancel_production_plan(doc_id: str) -> dict:
    """생산계획을 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="생산계획을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "생산계획이 취소되었습니다"}


@router.post(
    "/{plan_id}/create-work-orders",
    status_code=201,
    dependencies=[Depends(require_permission("production_plan:create"))],
)
def create_work_orders_from_plan(plan_id: str) -> dict:
    """생산계획에서 작업지시를 일괄 생성한다."""
    svc = WorkOrderService(tenant_id="default")
    wo_ids = svc.create_from_production_plan(plan_id)
    return {"production_plan_id": plan_id, "work_order_ids": wo_ids, "count": len(wo_ids)}
