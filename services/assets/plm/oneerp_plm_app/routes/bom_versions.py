"""BOM 버전(BOMVersion) API 라우터."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_plm_app.models.bom_version import BOMItem, BOMVersion, BOMVersionCreate
from oneerp_plm_app.services.bom_service import BOMService

router = APIRouter(prefix="/api/v1/plm/bom-versions", tags=["PLM BOM"])

_COLLECTION = "bom_versions"
_PREFIX = "BV"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("plm_bom:create"))])
def BOM_생성(body: BOMVersionCreate, user: CurrentUserDep) -> dict[str, Any]:
    """BOM 버전을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    bom_items = []
    for idx, item in enumerate(body.items, start=1):
        bom_items.append(
            BOMItem(
                line_no=idx,
                item_code=item.item_code,
                item_name=item.item_name,
                quantity=item.quantity,
                uom=item.uom,
                unit_cost=item.unit_cost,
                find_number=item.find_number,
                reference_designator=item.reference_designator,
                is_phantom=item.is_phantom,
                substitute_group=item.substitute_group,
                child_bom_id=item.child_bom_id,
                notes=item.notes,
            )
        )

    doc = BOMVersion(
        _id=doc_id,
        tenant_id=user.tenant_id,
        product_id=body.product_id,
        bom_type=body.bom_type,
        base_quantity=body.base_quantity,
        items=bom_items,
        eco_id=body.eco_id,
        parent_version_id=body.parent_version_id,
        source_ebom_id=body.source_ebom_id,
        effectivity_start=body.effectivity_start,
        effectivity_end=body.effectivity_end,
        notes=body.notes,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {"id": doc_id, "message": "BOM 버전이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("plm_bom:read"))])
def BOM_목록(
    user: CurrentUserDep,
    product_id: str | None = None,
    bom_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """BOM 버전 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if product_id:
        query["product_id"] = product_id
    if bom_type:
        query["bom_type"] = bom_type
    if status:
        query["status"] = status
    skip = (page - 1) * page_size
    items = repo.find_many(query, skip=skip, limit=page_size)
    return {"items": items, "page": page, "page_size": page_size}


@router.get("/{bom_version_id}", dependencies=[Depends(require_permission("plm_bom:read"))])
def BOM_상세(bom_version_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """BOM 버전 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(bom_version_id)
    if not doc:
        raise_not_found(f"BOM 버전을 찾을 수 없습니다: {bom_version_id}")
    return cast("dict[str, Any]", doc)


@router.post(
    "/{bom_version_id}/release",
    dependencies=[Depends(require_permission("plm_bom:write"))],
)
def BOM_릴리즈(bom_version_id: str, body: dict[str, Any], user: CurrentUserDep) -> dict[str, Any]:
    """BOM을 릴리즈한다."""
    service = BOMService(tenant_id=user.tenant_id)
    return service.release_bom(
        bom_version_id=bom_version_id,
        approved_by=body.get("approved_by", user.sub),
    )


@router.get(
    "/{bom_id_1}/compare/{bom_id_2}",
    dependencies=[Depends(require_permission("plm_bom:read"))],
)
def BOM_비교(bom_id_1: str, bom_id_2: str, user: CurrentUserDep) -> dict[str, Any]:
    """두 BOM 버전을 비교한다."""
    service = BOMService(tenant_id=user.tenant_id)
    return service.compare_bom(bom_id_1, bom_id_2)


@router.post(
    "/{ebom_id}/convert-to-mbom",
    status_code=201,
    dependencies=[Depends(require_permission("plm_bom:create"))],
)
def EBOM_MBOM_전환(ebom_id: str, body: dict[str, Any], user: CurrentUserDep) -> dict[str, Any]:
    """E-BOM을 M-BOM으로 전환한다."""
    service = BOMService(tenant_id=user.tenant_id)
    return service.convert_ebom_to_mbom(
        ebom_id=ebom_id,
        notes=body.get("notes", ""),
        user_id=user.sub,
    )
