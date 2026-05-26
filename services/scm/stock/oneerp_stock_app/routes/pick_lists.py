"""피킹목록(PickList) CRUD 라우트."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel, Field

from ..models.pick_list import PickList, PickListCreate, PickListItem, PickListUpdate

router = APIRouter(prefix="/api/v1/pick-lists", tags=["피킹목록"])

_COLLECTION = "pick_lists"
_PREFIX = "PL"


def _get_repo() -> Repository:
    """피킹목록 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


class _SalesOrderPickListItemCreate(BaseModel):
    item_code: str = Field(description="품목 코드")
    qty: float = Field(default=0, description="수량")
    warehouse: str = Field(default="", description="창고")


class _SalesOrderPickListCreate(BaseModel):
    sales_order_id: str
    tenant_id: str
    customer_id: str | None = None
    items: list[_SalesOrderPickListItemCreate] = []


@router.post("", status_code=201, dependencies=[Depends(require_permission("pick_list:create"))])
def create_pick_list(body: PickListCreate) -> dict:
    """피킹목록을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = PickList(
        purpose=body.purpose,
        items=body.items,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "피킹목록이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("pick_list:read"))])
def list_pick_lists(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """피킹목록 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.post("/from-sales-order", status_code=201)
def create_pick_list_from_sales_order(body: _SalesOrderPickListCreate) -> dict:
    """이벤트 payload로 전달된 판매주문 기준 피킹목록 초안을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX, tenant_id=body.tenant_id)
    doc = PickList(
        _id=doc_id,
        tenant_id=body.tenant_id,
        purpose="delivery",
        items=[
            PickListItem(
                item_code=item.item_code,
                qty=Decimal(str(item.qty)),
                warehouse=item.warehouse,
            )
            for item in body.items
        ],
        created_by="system:event",
        updated_by="system:event",
    )
    repo.insert(doc)
    return {
        "id": doc_id,
        "sales_order_id": body.sales_order_id,
        "message": "판매주문 기준 피킹목록이 생성되었습니다",
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("pick_list:read"))])
def get_pick_list(doc_id: str) -> dict:
    """피킹목록을 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="피킹목록을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("pick_list:write"))])
def update_pick_list(doc_id: str, body: PickListUpdate) -> dict:
    """피킹목록을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="피킹목록을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "피킹목록이 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("pick_list:submit"))])
def submit_pick_list(doc_id: str, user: CurrentUserDep) -> dict:
    """피킹목록을 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="피킹목록을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.PICK_LIST_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"message": "피킹목록이 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("pick_list:cancel"))])
def cancel_pick_list(doc_id: str) -> dict:
    """피킹목록을 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="피킹목록을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "피킹목록이 취소되었습니다"}
