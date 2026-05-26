"""경비유형(ExpenseType) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from ..models.expense_type import ExpenseType, ExpenseTypeCreate, ExpenseTypeUpdate
from ..services.expense_route_service import ExpenseRouteService

router = APIRouter(prefix="/api/v1/expense-types", tags=["경비유형"])
_COLLECTION = "expense_types"
_PREFIX = "EXT"


def _get_service(tenant_id: str) -> ExpenseRouteService:
    """요청 테넌트에 바인딩된 route service를 반환한다."""
    return ExpenseRouteService(_COLLECTION, tenant_id)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("expense_type:create"))]
)
async def create_expense_type(body: ExpenseTypeCreate, user: CurrentUserDep) -> dict:
    """경비유형을 생성한다."""
    service = _get_service(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = ExpenseType(_id=doc_id, **body.model_dump())
    service.create(doc)
    return {"id": doc_id, "message": "경비유형이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("expense_type:read"))])
async def list_expense_types(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """경비유형 목록을 페이지네이션으로 조회한다."""
    service = _get_service(user.tenant_id)
    return service.list_page(page=page, page_size=page_size)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("expense_type:read"))])
async def get_expense_type(doc_id: str, user: CurrentUserDep) -> dict:
    """경비유형 상세 정보를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_or_raise(doc_id, detail="경비유형을 찾을 수 없습니다")


@router.put("/{doc_id}", dependencies=[Depends(require_permission("expense_type:write"))])
async def update_expense_type(doc_id: str, body: ExpenseTypeUpdate, user: CurrentUserDep) -> dict:
    """경비유형을 수정한다."""
    service = _get_service(user.tenant_id)
    service.get_or_raise(doc_id, detail="경비유형을 찾을 수 없습니다")
    service.update(doc_id, body.model_dump(exclude_none=True))
    return {"message": "경비유형이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("expense_type:delete"))])
async def delete_expense_type(doc_id: str, user: CurrentUserDep) -> dict:
    """경비유형을 삭제한다."""
    service = _get_service(user.tenant_id)
    service.get_or_raise(doc_id, detail="경비유형을 찾을 수 없습니다")
    service.delete(doc_id)
    return {"message": "경비유형이 삭제되었습니다"}
