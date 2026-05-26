"""법인카드거래(CorporateCardTransaction) 로그 라우트 — POST+GET만."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from ..models.corporate_card_transaction import (
    CorporateCardTransaction,
    CorporateCardTransactionCreate,
)
from ..services.expense_route_service import ExpenseRouteService

router = APIRouter(prefix="/api/v1/corporate-card-transactions", tags=["법인카드거래"])
_COLLECTION = "corporate_card_transactions"
_PREFIX = "CCT"


def _get_service(tenant_id: str) -> ExpenseRouteService:
    """요청 테넌트에 바인딩된 route service를 반환한다."""
    return ExpenseRouteService(_COLLECTION, tenant_id)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("corporate_card_transaction:create"))],
)
async def create_corporate_card_transaction(
    body: CorporateCardTransactionCreate,
    user: CurrentUserDep,
) -> dict:
    """법인카드거래를 생성한다."""
    service = _get_service(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = CorporateCardTransaction(_id=doc_id, **body.model_dump())
    service.create(doc)
    return {
        "corporate_card_transaction_id": doc_id,
        "message": "법인카드거래가 생성되었습니다",
    }


@router.get("/", dependencies=[Depends(require_permission("corporate_card_transaction:read"))])
async def list_corporate_card_transactions(
    user: CurrentUserDep, page: int = 1, page_size: int = 20
) -> dict:
    """법인카드거래 목록을 페이지네이션으로 조회한다."""
    service = _get_service(user.tenant_id)
    return service.list_page(page=page, page_size=page_size)


@router.get(
    "/{doc_id}", dependencies=[Depends(require_permission("corporate_card_transaction:read"))]
)
async def get_corporate_card_transaction(doc_id: str, user: CurrentUserDep) -> dict:
    """법인카드거래 상세 정보를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_or_raise(doc_id, detail="법인카드거래를 찾을 수 없습니다")
