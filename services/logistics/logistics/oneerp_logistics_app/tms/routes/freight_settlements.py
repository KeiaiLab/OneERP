"""운임 정산(FreightSettlement) API 라우터."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_logistics_app.tms.models.freight_settlement import (
    FreightSettlement,
    FreightSettlementCreate,
)
from oneerp_logistics_app.tms.services.freight_service import FreightService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/freight-settlements", tags=["운임정산"])

_COLLECTION = "freight_settlements"
_PREFIX = "FS"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("freight_settlement:create"))]
)
def 운임정산_생성(body: FreightSettlementCreate, user: CurrentUserDep) -> dict[str, Any]:
    """운임 정산을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    # 정산 금액 계산
    freight_svc = FreightService(user.tenant_id)
    calc = freight_svc.calculate_settlement(
        subtotal=body.subtotal_amount,
        fuel_surcharge=body.fuel_surcharge,
        additional_charges=[c.model_dump() for c in body.additional_charges]
        if body.additional_charges
        else None,
        deductions=[d.model_dump() for d in body.deductions] if body.deductions else None,
        currency=body.currency,
    )

    doc = FreightSettlement(
        _id=doc_id,
        tenant_id=user.tenant_id,
        settlement_no=doc_id,
        carrier_id=body.carrier_id,
        period_from=body.period_from,
        period_to=body.period_to,
        shipment_ids=body.shipment_ids,
        total_shipments=len(body.shipment_ids),
        subtotal_amount=body.subtotal_amount,
        fuel_surcharge=body.fuel_surcharge,
        additional_charges=body.additional_charges or [],
        deductions=body.deductions or [],
        tax_amount=calc["tax_amount"],
        total_amount=calc["total_amount"],
        currency=body.currency,
        status="draft",
        notes=body.notes,
        company=body.company,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {
        "_id": doc_id,
        "settlement_no": doc_id,
        "status": "draft",
        "total_amount": calc["total_amount"],
    }


@router.get("", dependencies=[Depends(require_permission("freight_settlement:read"))])
def 운임정산_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """운임 정산 목록을 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("freight_settlement:read"))])
def 운임정산_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """운임 정산 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("운임 정산을 찾을 수 없습니다")
    assert doc is not None
    return doc


@router.post(
    "/{doc_id}/confirm",
    dependencies=[Depends(require_permission("freight_settlement:write"))],
)
def 운임정산_확정(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """운임 정산을 확정한다 (draft → confirmed)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("운임 정산을 찾을 수 없습니다")
    assert doc is not None

    if doc.get("status") != "draft":
        raise OneERPError(
            status_code=422,
            error="ERR-TMS-109",
            detail="초안 상태에서만 확정할 수 있습니다",
        )

    repo.update_by_id(doc_id, {"status": "confirmed", "updated_by": user.sub})
    logger.info("운임 정산 확정: %s (운송사: %s)", doc_id, doc.get("carrier_id"))
    return {"id": doc_id, "status": "confirmed", "message": "운임 정산이 확정되었습니다"}
