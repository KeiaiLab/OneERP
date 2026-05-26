"""포괄주문(Blanket Order) API 라우터.

M3 arch-baseline 감소: Route → Service 3층 (sales_returns 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.permissions import require_permission

from oneerp_selling_app.models.blanket_order import BlanketOrderCreate, BlanketOrderUpdate
from oneerp_selling_app.services.blanket_order_service import BlanketOrderService

router = APIRouter(prefix="/api/v1/blanket-orders", tags=["포괄주문"])


def _service(user: CurrentUserDep) -> BlanketOrderService:
    return BlanketOrderService(tenant_id=user.tenant_id, user_sub=user.sub)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("blanket_order:create"))]
)
def 포괄주문_생성(body: BlanketOrderCreate, user: CurrentUserDep) -> dict[str, Any]:
    """포괄주문을 생성한다."""
    return _service(user).create_from_request(body)


@router.get("", dependencies=[Depends(require_permission("blanket_order:read"))])
def 포괄주문_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """포괄주문 목록을 페이지네이션으로 조회한다."""
    skip = (page - 1) * page_size
    result = _service(user).list_orders(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("blanket_order:read"))])
def 포괄주문_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """포괄주문 상세 정보를 조회한다."""
    doc = _service(user).get_order(doc_id)
    if not doc:
        raise_not_found("포괄주문을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("blanket_order:write"))])
def 포괄주문_수정(
    doc_id: str,
    body: BlanketOrderUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """포괄주문을 수정한다. 초안 상태에서만 허용."""
    return _service(user).update_order(doc_id, body)


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("blanket_order:submit"))])
def 포괄주문_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """포괄주문을 제출한다 (초안 → 제출)."""
    return _service(user).submit_order(doc_id)


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("blanket_order:cancel"))])
def 포괄주문_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """포괄주문을 취소한다 (제출 → 취소)."""
    return _service(user).cancel_order(doc_id)
