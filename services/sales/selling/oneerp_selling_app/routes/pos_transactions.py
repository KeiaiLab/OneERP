"""POS 거래(POSTransaction) CRUD 라우터.

M3 arch-baseline 감소: Route → Service 3층 (blanket_orders 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.permissions import require_permission

from oneerp_selling_app.models.pos_transaction import POSTransactionCreate, POSTransactionUpdate
from oneerp_selling_app.services.pos_transaction_service import POSTransactionService

router = APIRouter(prefix="/api/v1/pos-transactions", tags=["POS 거래"])


def _service(user: CurrentUserDep) -> POSTransactionService:
    return POSTransactionService(tenant_id=user.tenant_id, user_sub=user.sub)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("pos_transaction:create"))]
)
def create_pos_transaction(body: POSTransactionCreate, user: CurrentUserDep) -> dict[str, Any]:
    """POS 거래를 생성한다."""
    return _service(user).create_from_request(body)


@router.get("", dependencies=[Depends(require_permission("pos_transaction:read"))])
def list_pos_transactions(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """POS 거래 목록을 페이지네이션으로 조회한다."""
    skip = (page - 1) * page_size
    result = _service(user).list_transactions(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("pos_transaction:read"))])
def get_pos_transaction(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """POS 거래 상세 정보를 조회한다."""
    doc = _service(user).get_transaction(doc_id)
    if not doc:
        raise_not_found("POS 거래를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("pos_transaction:write"))])
def update_pos_transaction(
    doc_id: str,
    body: POSTransactionUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """POS 거래를 수정한다. 제출된 거래는 수정할 수 없다 (BR-SELL-011 감사 기록)."""
    return _service(user).update_transaction(doc_id, body)


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("pos_transaction:submit"))]
)
def submit_pos_transaction(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """POS 거래를 제출한다 (초안 → 제출)."""
    return _service(user).submit_transaction(doc_id)


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("pos_transaction:delete"))],
)
def delete_pos_transaction(doc_id: str, user: CurrentUserDep) -> None:
    """POS 거래를 삭제한다. 제출된 거래는 삭제할 수 없다 (BR-SELL-011 감사 기록)."""
    _service(user).delete_transaction(doc_id)
