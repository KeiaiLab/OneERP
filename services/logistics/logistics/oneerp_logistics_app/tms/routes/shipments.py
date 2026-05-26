"""��송 건(Shipment) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_logistics_app.tms.models.shipment import Shipment, ShipmentCreate, ShipmentUpdate
from oneerp_logistics_app.tms.services.dispatch_service import DispatchService

router = APIRouter(prefix="/api/v1/shipments", tags=["배송건"])

_COLLECTION = "shipments"
_PREFIX = "SHP"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("shipment:create"))])
def 배송건_생성(body: ShipmentCreate, user: CurrentUserDep) -> dict[str, Any]:
    """배송 건을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    # 총 중량/용적 자동 계산
    total_weight = sum(item.weight_kg for item in body.items)
    total_volume = sum(item.volume_cbm for item in body.items)

    doc = Shipment(
        _id=doc_id,
        tenant_id=user.tenant_id,
        shipment_no=doc_id,
        delivery_note_id=body.delivery_note_id,
        sales_order_id=body.sales_order_id,
        ship_from=body.ship_from,
        ship_to=body.ship_to,
        items=body.items,
        total_weight_kg=total_weight,
        total_volume_cbm=total_volume,
        total_packages=len(body.items),
        expected_pickup=body.expected_pickup,
        expected_delivery=body.expected_delivery,
        special_instructions=body.special_instructions,
        delivery_condition_id=body.delivery_condition_id,
        is_return=body.is_return,
        company=body.company,
        status="draft",
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {
        "_id": doc_id,
        "shipment_no": doc_id,
        "status": "draft",
        "total_weight_kg": total_weight,
    }


@router.get("", dependencies=[Depends(require_permission("shipment:read"))])
def 배송건_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """배송 건 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    query: dict[str, Any] = {}
    if status:
        query["status"] = status
    docs = repo.find_many(query=query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count(query=query)
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("shipment:read"))])
def 배송건_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """배송 건 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배송 건을 찾을 수 없습니다")
    assert doc is not None
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("shipment:write"))])
def 배송건_수정(
    doc_id: str,
    body: ShipmentUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """배송 건을 수정한다. draft 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배송 건을 찾을 수 없습니다")
    assert doc is not None
    if doc.get("status") != "draft":
        raise OneERPError(
            status_code=422,
            error="ERR-TMS-109",
            detail="초안 상태에서만 수정할 수 있습니다",
        )

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        update_data["total_weight_kg"] = sum(
            i.get("weight_kg", 0) if isinstance(i, dict) else i.weight_kg
            for i in update_data["items"]
        )
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "배송 건이 수정되었습니다"}


@router.post(
    "/{doc_id}/transition",
    dependencies=[Depends(require_permission("shipment:write"))],
)
def 배송건_상태전이(
    doc_id: str,
    user: CurrentUserDep,
    target_status: str = "dispatched",
) -> dict[str, Any]:
    """배송 건 상태를 전이한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배송 건을 찾을 수 없습니다")
    assert doc is not None

    dispatch_svc = DispatchService(user.tenant_id)
    current = doc.get("status", "draft")
    dispatch_svc.validate_shipment_transition(current, target_status)

    # BR-TMS-007: POD 필수 검증
    if (
        target_status == "delivered"
        and dispatch_svc.check_pod_required(doc)
        and not doc.get("pod_id")
    ):
        raise OneERPError(
            status_code=422,
            error="ERR-TMS-105",
            detail="배송 증빙(POD)이 필요합니다",
        )

    repo.update_by_id(doc_id, {"status": target_status, "updated_by": user.sub})
    return {
        "id": doc_id,
        "status": target_status,
        "message": f"상태가 {target_status}(으)로 변경되었습니다",
    }
