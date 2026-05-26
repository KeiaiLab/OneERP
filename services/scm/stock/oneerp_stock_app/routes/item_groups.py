"""품목그룹(ItemGroup) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.item_group import ItemGroup, ItemGroupCreate, ItemGroupUpdate

router = APIRouter(prefix="/api/v1/item-groups", tags=["품목그룹"])

_COLLECTION = "item_groups"
_PREFIX = "IG"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("item_group:create"))])
def create_item_group(body: ItemGroupCreate, user: CurrentUserDep) -> dict:
    """품목그룹을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    doc = ItemGroup(
        tenant_id=user.tenant_id,
        group_name=body.group_name,
        parent_group=body.parent_group,
        is_group=body.is_group,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "품목그룹이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("item_group:read"))])
def list_item_groups(
    user: CurrentUserDep,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """품목그룹 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("item_group:read"))])
def get_item_group(doc_id: str, user: CurrentUserDep) -> dict:
    """품목그룹을 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품목그룹을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("item_group:write"))])
def update_item_group(doc_id: str, body: ItemGroupUpdate, user: CurrentUserDep) -> dict:
    """품목그룹을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품목그룹을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "품목그룹이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=200, dependencies=[Depends(require_permission("item_group:delete"))]
)
def delete_item_group(doc_id: str, user: CurrentUserDep) -> dict:
    """품목그룹을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품목그룹을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "품목그룹이 삭제되었습니다"}
