"""BOM(Bill of Materials) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_manufacturing_app.models.bom import BOM, BOMCreate, BOMUpdate

router = APIRouter(prefix="/api/v1/boms", tags=["BOM"])

_COLLECTION = "boms"
_PREFIX = "BOM"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("bom:create"))])
def create_bom(body: BOMCreate, user: CurrentUserDep) -> dict[str, Any]:
    """BOM을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    # BR-MFG-003: 기본 BOM 유일성 — 동일 item_code에 is_default=true 최대 1개
    if body.is_default:
        existing_defaults = repo.find_many(
            {"item_code": body.item_code, "is_default": True},
            limit=100,
        )
        for existing in existing_defaults:
            repo.update_by_id(existing["_id"], {"is_default": False})

    bom = BOM(
        _id=doc_id,
        tenant_id=user.tenant_id,
        item_code=body.item_code,
        item_name=body.item_name,
        quantity=body.quantity,
        items=body.items,
        is_active=body.is_active,
        is_default=body.is_default,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(bom)
    return {"id": doc_id, "message": "BOM이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("bom:read"))])
def list_boms(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """BOM 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("bom:read"))])
def get_bom(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BOM 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("BOM을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("bom:write"))])
def update_bom(
    doc_id: str,
    body: BOMUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """BOM을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("BOM을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub

    # BR-MFG-003: 기본 BOM 유일성 — PUT으로 is_default=True 설정 시 기존 기본 BOM 해제
    if update_data.get("is_default") is True:
        item_code = doc.get("item_code", "")
        existing_defaults = repo.find_many(
            {"item_code": item_code, "is_default": True, "_id": {"$ne": doc_id}},
            limit=10,
        )
        for existing in existing_defaults:
            repo.update_by_id(existing["_id"], {"is_default": False})

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "BOM이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("bom:delete"))]
)
def delete_bom(doc_id: str, user: CurrentUserDep) -> None:
    """BR-MFG-005: BOM 삭제 — 초안(draft) 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("BOM을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    # BR-MFG-005: 제출(submitted) 또는 취소(cancelled) 상태의 BOM은 삭제 불가
    docstatus = doc.get("docstatus", 0)
    if docstatus != 0:
        raise_bad_request("제출되었거나 취소된 BOM은 삭제할 수 없습니다")

    repo.delete_by_id(doc_id)


@router.get("/{doc_id}/tree", dependencies=[Depends(require_permission("bom:read"))])
def get_bom_tree(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BOM 트리를 조회한다 — 1단계 전개."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("BOM을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return {"bom": doc, "children": doc.get("items", [])}
