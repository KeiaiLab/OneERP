"""판매반품(Sales Return) API 라우터.

M3 arch-baseline 감소: Route → Service 3층 (channels/messages 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from oneerp_selling_app.models.sales_return import SalesReturnCreate, SalesReturnUpdate
from oneerp_selling_app.services.sales_return_service import SalesReturnService

router = APIRouter(prefix="/api/v1/sales-returns", tags=["판매반품"])


def _service(user: CurrentUserDep) -> SalesReturnService:
    return SalesReturnService(tenant_id=user.tenant_id, user_sub=user.sub)


@router.post("", status_code=201, dependencies=[Depends(require_permission("sales_return:create"))])
def 판매반품_생성(body: SalesReturnCreate, user: CurrentUserDep) -> dict[str, Any]:
    """판매반품을 생성한다."""
    return _service(user).create_from_request(body)


@router.get("", dependencies=[Depends(require_permission("sales_return:read"))])
def 판매반품_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """판매반품 목록을 페이지네이션으로 조회한다."""
    skip = (page - 1) * page_size
    result = _service(user).list_returns(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("sales_return:read"))])
def 판매반품_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매반품 상세 정보를 조회한다."""
    from oneerp_core.errors import raise_not_found

    doc = _service(user).get_return(doc_id)
    if not doc:
        raise_not_found("판매반품을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("sales_return:write"))])
def 판매반품_수정(
    doc_id: str,
    body: SalesReturnUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """판매반품을 수정한다. 초안 상태에서만 허용."""
    return _service(user).update_return(doc_id, body)


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("sales_return:submit"))])
def 판매반품_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매반품을 제출한다 (초안 → 제출)."""
    return _service(user).submit_return(doc_id)


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("sales_return:cancel"))])
def 판매반품_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매반품을 취소한다 (제출 → 취소)."""
    return _service(user).cancel_return(doc_id)
