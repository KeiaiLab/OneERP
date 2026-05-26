"""제품 마스터(Product) API 라우터."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_conflict, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_plm_app.models.product import Product, ProductCreate, ProductUpdate
from oneerp_plm_app.services.product_lifecycle_service import ProductLifecycleService

router = APIRouter(prefix="/api/v1/plm/products", tags=["PLM 제품"])

_COLLECTION = "products"
_PREFIX = "PRD"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("plm_product:create"))])
def 제품_생성(body: ProductCreate, user: CurrentUserDep) -> dict[str, Any]:
    """제품 마스터를 생성한다."""
    repo = _get_repo(user.tenant_id)

    # 제품 코드 중복 검증
    existing = next(iter(repo.find_many({"product_code": body.product_code}, limit=1)), None)
    if existing:
        raise_conflict(f"제품 코드가 이미 존재합니다: {body.product_code}")

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    doc = Product(
        _id=doc_id,
        tenant_id=user.tenant_id,
        product_code=body.product_code,
        product_name=body.product_name,
        product_type=body.product_type,
        category_id=body.category_id,
        family_id=body.family_id,
        description=body.description,
        uom=body.uom,
        weight=body.weight,
        dimensions=body.dimensions,
        attributes=body.attributes,
        tags=body.tags,
        thumbnail_url=body.thumbnail_url,
        responsible_engineer=body.responsible_engineer,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {"id": doc_id, "message": "제품이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("plm_product:read"))])
def 제품_목록(
    user: CurrentUserDep,
    lifecycle_status: str | None = None,
    product_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """제품 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if lifecycle_status:
        query["lifecycle_status"] = lifecycle_status
    if product_type:
        query["product_type"] = product_type
    skip = (page - 1) * page_size
    items = repo.find_many(query, skip=skip, limit=page_size)
    return {"items": items, "page": page, "page_size": page_size}


@router.get("/{product_id}", dependencies=[Depends(require_permission("plm_product:read"))])
def 제품_상세(product_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """제품 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(product_id)
    if not doc:
        raise_not_found(f"제품을 찾을 수 없습니다: {product_id}")
    return cast("dict[str, Any]", doc)


@router.patch("/{product_id}", dependencies=[Depends(require_permission("plm_product:write"))])
def 제품_수정(product_id: str, body: ProductUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """제품 정보를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(product_id)
    if not doc:
        raise_not_found(f"제품을 찾을 수 없습니다: {product_id}")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(product_id, update_data)
    return {"id": product_id, "message": "제품이 수정되었습니다"}


@router.post(
    "/{product_id}/lifecycle",
    dependencies=[Depends(require_permission("plm_product:write"))],
)
def 수명주기_전이(
    product_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제품 수명주기 상태를 전이한다."""
    service = ProductLifecycleService(tenant_id=user.tenant_id)
    return service.transition_lifecycle(
        product_id=product_id,
        new_status=body.get("new_status", ""),
        reason=body.get("reason", ""),
        user_id=user.sub,
    )
