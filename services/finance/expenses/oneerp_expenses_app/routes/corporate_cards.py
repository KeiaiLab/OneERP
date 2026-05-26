"""법인카드(CorporateCard) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from ..models.corporate_card import (
    CorporateCard,
    CorporateCardCreate,
    CorporateCardUpdate,
)
from ..services.expense_route_service import ExpenseRouteService

router = APIRouter(prefix="/api/v1/corporate-cards", tags=["법인카드"])
_COLLECTION = "corporate_cards"
_PREFIX = "CC"


def _get_service(tenant_id: str) -> ExpenseRouteService:
    """요청 테넌트에 바인딩된 route service를 반환한다."""
    return ExpenseRouteService(_COLLECTION, tenant_id)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("corporate_card:create"))]
)
async def create_corporate_card(body: CorporateCardCreate, user: CurrentUserDep) -> dict:
    """법인카드를 생성한다."""
    service = _get_service(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = CorporateCard(_id=doc_id, **body.model_dump())
    service.create(doc)
    return {"corporate_card_id": doc_id, "message": "법인카드가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("corporate_card:read"))])
async def list_corporate_cards(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """법인카드 목록을 페이지네이션으로 조회한다."""
    service = _get_service(user.tenant_id)
    return service.list_page(page=page, page_size=page_size)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("corporate_card:read"))])
async def get_corporate_card(doc_id: str, user: CurrentUserDep) -> dict:
    """법인카드 상세 정보를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_or_raise(doc_id, detail="법인카드를 찾을 수 없습니다")


@router.put("/{doc_id}", dependencies=[Depends(require_permission("corporate_card:write"))])
async def update_corporate_card(
    doc_id: str, body: CorporateCardUpdate, user: CurrentUserDep
) -> dict:
    """법인카드를 수정한다."""
    service = _get_service(user.tenant_id)
    service.get_or_raise(doc_id, detail="법인카드를 찾을 수 없습니다")
    service.update(doc_id, body.model_dump(exclude_none=True))
    return {"message": "법인카드가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("corporate_card:delete"))])
async def delete_corporate_card(doc_id: str, user: CurrentUserDep) -> dict:
    """법인카드를 삭제한다."""
    service = _get_service(user.tenant_id)
    service.get_or_raise(doc_id, detail="법인카드를 찾을 수 없습니다")
    service.delete(doc_id)
    return {"message": "법인카드가 삭제되었습니다"}
