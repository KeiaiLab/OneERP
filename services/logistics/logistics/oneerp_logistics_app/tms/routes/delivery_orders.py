"""배차 지시(DeliveryOrder) API 라우터."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_logistics_app.tms.models.delivery_order import DeliveryOrder, DeliveryOrderCreate
from oneerp_logistics_app.tms.services.dispatch_service import DispatchService
from oneerp_logistics_app.tms.services.freight_service import FreightService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/delivery-orders", tags=["배차지시"])

_COLLECTION = "delivery_orders"
_PREFIX = "DO"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("delivery_order:create"))]
)
def 배차지시_생성(body: DeliveryOrderCreate, user: CurrentUserDep) -> dict[str, Any]:
    """배차 지시를 생성한다."""
    dispatch_svc = DispatchService(user.tenant_id)

    # 배송 건 검증
    shipments = dispatch_svc.validate_shipments_for_dispatch(body.shipment_ids)

    # 운송사 검증
    dispatch_svc.validate_carrier(body.carrier_id)

    # 총 중량/용적 합산
    total_weight = sum(float(s.get("total_weight_kg", 0)) for s in shipments)
    total_volume = sum(float(s.get("total_volume_cbm", 0)) for s in shipments)

    # 차량 검증 (차량 배정 시)
    if body.vehicle_id:
        temp_req = "normal"
        for shp in shipments:
            req = dispatch_svc.get_temperature_requirement(shp)
            if req != "normal":
                temp_req = req
                break
        dispatch_svc.validate_vehicle(
            body.vehicle_id,
            total_weight_kg=total_weight,
            temperature_requirement=temp_req,
        )

    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    doc = DeliveryOrder(
        _id=doc_id,
        tenant_id=user.tenant_id,
        order_no=doc_id,
        dispatch_date=body.dispatch_date,
        carrier_id=body.carrier_id,
        vehicle_id=body.vehicle_id,
        driver_name=body.driver_name,
        driver_phone=body.driver_phone,
        shipment_ids=body.shipment_ids,
        route_id=body.route_id,
        total_weight_kg=total_weight,
        total_volume_cbm=total_volume,
        total_shipments=len(body.shipment_ids),
        planned_sequence=body.planned_sequence or [],
        status="draft",
        dispatch_method=body.dispatch_method,
        notes=body.notes,
        company=body.company,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)

    # 배송 건에 배차 지시 ID 연결
    shp_repo = Repository("shipments", tenant_id=user.tenant_id)
    for sid in body.shipment_ids:
        shp_repo.update_by_id(sid, {"delivery_order_id": doc_id})

    return {
        "_id": doc_id,
        "order_no": doc_id,
        "status": "draft",
        "total_weight_kg": total_weight,
        "total_shipments": len(body.shipment_ids),
    }


@router.get("", dependencies=[Depends(require_permission("delivery_order:read"))])
def 배차지시_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """배차 지시 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("delivery_order:read"))])
def 배차지시_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """배차 지시 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배차 지시를 찾을 수 없습니다")
    assert doc is not None
    return doc


@router.post(
    "/{doc_id}/confirm",
    dependencies=[Depends(require_permission("delivery_order:write"))],
)
def 배차지시_확정(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """배차 지시를 확정한다 (draft → confirmed).

    BR-TMS-001: 운송사/차량 필수 검증
    BR-TMS-005: 운임 자동 계산
    """
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배차 지시를 찾을 수 없습니다")
    assert doc is not None

    dispatch_svc = DispatchService(user.tenant_id)
    dispatch_svc.validate_do_transition(doc.get("status", "draft"), "confirmed")

    carrier_id = doc.get("carrier_id", "")
    vehicle_id = doc.get("vehicle_id")
    carrier = dispatch_svc.validate_carrier(carrier_id)

    # BR-TMS-001: 택배 유형은 차량 불필요
    carrier_type = carrier.get("carrier_type", "")
    if carrier_type != "parcel" and not vehicle_id:
        raise OneERPError(
            status_code=422,
            error="ERR-TMS-101",
            detail="운송사와 차량을 배정해야 합니다",
        )

    # 운임 계산
    freight_svc = FreightService(user.tenant_id)
    shp_repo = Repository("shipments", tenant_id=user.tenant_id)

    for sid in doc.get("shipment_ids", []):
        shp = shp_repo.find_by_id(sid)
        if shp:
            dispatch_date = doc.get("dispatch_date")
            assert isinstance(dispatch_date, date)
            calc = freight_svc.calculate_freight(
                carrier_id=carrier_id,
                route_id=doc.get("route_id"),
                vehicle_type=None,
                total_weight_kg=float(shp.get("total_weight_kg", 0)),
                dispatch_date=dispatch_date,
            )
            shp_repo.update_by_id(
                sid,
                {
                    "carrier_id": carrier_id,
                    "vehicle_id": vehicle_id,
                    "freight_amount": calc["freight_amount"],
                    "status": "dispatched",
                    "updated_by": user.sub,
                },
            )

    # 차량 상태 변경
    if vehicle_id:
        v_repo = Repository("vehicles", tenant_id=user.tenant_id)
        v_repo.update_by_id(vehicle_id, {"status": "in_transit"})

    repo.update_by_id(doc_id, {"status": "confirmed", "updated_by": user.sub})

    logger.info("배차 확정 완료: %s (운송사: %s, 차량: %s)", doc_id, carrier_id, vehicle_id)
    return {"id": doc_id, "status": "confirmed", "message": "배차가 확정되었습니다"}


@router.post(
    "/{doc_id}/cancel",
    dependencies=[Depends(require_permission("delivery_order:write"))],
)
def 배차지시_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """배차 지시를 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("배차 지시를 찾을 수 없습니다")
    assert doc is not None

    dispatch_svc = DispatchService(user.tenant_id)
    dispatch_svc.validate_do_transition(doc.get("status", "draft"), "cancelled")

    # 배송 건 상태 복원
    shp_repo = Repository("shipments", tenant_id=user.tenant_id)
    for sid in doc.get("shipment_ids", []):
        shp_repo.update_by_id(
            sid,
            {
                "status": "draft",
                "delivery_order_id": None,
                "carrier_id": None,
                "vehicle_id": None,
                "updated_by": user.sub,
            },
        )

    # 차량 상태 복원
    vehicle_id = doc.get("vehicle_id")
    if vehicle_id:
        v_repo = Repository("vehicles", tenant_id=user.tenant_id)
        v_repo.update_by_id(vehicle_id, {"status": "available"})

    repo.update_by_id(doc_id, {"status": "cancelled", "updated_by": user.sub})
    return {"id": doc_id, "status": "cancelled", "message": "배차가 취소되었습니다"}
