"""자재요청(Material Request) 사용자 흐름 라우터."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.material_request import (
    MaterialRequest,
    MaterialRequestCreate,
    MaterialRequestCreateRFQ,
    MaterialRequestItem,
    MaterialRequestUpdate,
)
from oneerp_buying_app.services.buyer_approval_service import BuyerApprovalService
from oneerp_buying_app.services.purchase_process_service import PurchaseProcessService

router = APIRouter(prefix="/api/v1/material-requests", tags=["자재요청"])

_COLLECTION = "material_requests"
_PREFIX = "MR"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _calculate_total_qty(items: list[dict[str, Any]]) -> float:
    """라인 아이템의 총 수량을 계산한다."""
    return sum(item.get("qty", 0) for item in items)


def _serialize_decimal(value: Any) -> float:
    """Decimal/정수를 API 저장용 float로 정규화한다."""
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _suggest_supplier_for_item(tenant_id: str, item: dict[str, Any]) -> dict[str, str]:
    """품목 기준 추천 공급업체를 조회한다."""
    pricing_repo = Repository("purchase_pricing_rules", tenant_id=tenant_id)
    supplier_repo = Repository("suppliers", tenant_id=tenant_id)
    scorecard_repo = Repository("supplier_scorecards", tenant_id=tenant_id)

    item_code = str(item.get("item_code", "")).strip()
    if item_code:
        pricing_rules = pricing_repo.find_many(
            {"item_code": item_code, "is_active": True},
            sort=[("priority", 1)],
            limit=1,
        )
        if pricing_rules:
            supplier_id = str(pricing_rules[0].get("supplier", "")).strip()
            if supplier_id:
                supplier = supplier_repo.find_by_id(supplier_id) or {}
                return {
                    "supplier_id": supplier_id,
                    "supplier_name": str(supplier.get("supplier_name", "")),
                    "source": "pricing_rule",
                }

    scorecards = scorecard_repo.find_many(sort=[("total_score", -1)], limit=1)
    if scorecards:
        supplier_id = str(scorecards[0].get("supplier", "")).strip()
        if supplier_id:
            supplier = supplier_repo.find_by_id(supplier_id) or {}
            return {
                "supplier_id": supplier_id,
                "supplier_name": str(supplier.get("supplier_name", "")),
                "source": "supplier_scorecard",
            }

    return {"supplier_id": "", "supplier_name": "", "source": ""}


def _enrich_items(
    tenant_id: str,
    items_raw: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], float, dict[str, str]]:
    """예상 금액과 추천 공급업체를 라인/문서 수준으로 계산한다."""
    enriched_items: list[dict[str, Any]] = []
    request_supplier_id = ""
    request_supplier_name = ""

    for item in items_raw:
        normalized = {**item}
        qty = _serialize_decimal(normalized.get("qty", 0))
        estimated_unit_cost = _serialize_decimal(normalized.get("estimated_unit_cost", 0))
        normalized["estimated_amount"] = round(qty * estimated_unit_cost, 2)
        suggestion = _suggest_supplier_for_item(tenant_id, normalized)
        normalized["suggested_supplier_id"] = suggestion["supplier_id"]
        normalized["suggested_supplier_name"] = suggestion["supplier_name"]
        normalized["suggestion_source"] = suggestion["source"]
        enriched_items.append(normalized)

        if suggestion["supplier_id"]:
            if not request_supplier_id:
                request_supplier_id = suggestion["supplier_id"]
                request_supplier_name = suggestion["supplier_name"]
            elif request_supplier_id != suggestion["supplier_id"]:
                request_supplier_id = ""
                request_supplier_name = ""

    estimated_total_amount = round(
        sum(_serialize_decimal(item.get("estimated_amount", 0)) for item in enriched_items),
        2,
    )
    return (
        enriched_items,
        estimated_total_amount,
        {
            "supplier_id": request_supplier_id,
            "supplier_name": request_supplier_name,
        },
    )


def _resolve_budget_status(doc: dict[str, Any], *, enforce: bool = False) -> str:
    """예산 상태를 계산한다."""
    budget_limit = _serialize_decimal(doc.get("budget_limit", 0))
    estimated_total_amount = _serialize_decimal(doc.get("estimated_total_amount", 0))
    if budget_limit <= 0:
        return "unchecked"
    if estimated_total_amount > budget_limit:
        if enforce:
            raise_unprocessable(
                "ERR-BUY-041",
                f"예산 한도({budget_limit:,.0f})를 초과했습니다. 예상 금액: {estimated_total_amount:,.0f}",
            )
        return "exceeded"
    return "within_budget"


def _pick_primary_item_group(items: list[dict[str, Any]]) -> str:
    """승인 라우팅에 사용할 대표 품목 그룹을 선택한다."""
    grouped_amounts: dict[str, float] = defaultdict(float)
    for item in items:
        item_group = str(item.get("item_group", "")).strip()
        if not item_group:
            continue
        grouped_amounts[item_group] += _serialize_decimal(item.get("estimated_amount", 0))
    if not grouped_amounts:
        return ""
    return max(grouped_amounts.items(), key=lambda entry: entry[1])[0]


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("material_request:create"))]
)
def 자재요청_생성(body: MaterialRequestCreate, user: CurrentUserDep) -> dict[str, Any]:
    """자재요청을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    items_raw, estimated_total_amount, request_supplier = _enrich_items(user.tenant_id, items_raw)
    total_qty = _calculate_total_qty(items_raw)
    budget_status = _resolve_budget_status(
        {
            "budget_limit": body.budget_limit,
            "estimated_total_amount": estimated_total_amount,
        },
    )

    material_request = MaterialRequest(
        _id=doc_id,
        tenant_id=user.tenant_id,
        request_type=body.request_type,
        required_date=body.required_date,
        budget_limit=body.budget_limit,
        budget_status=budget_status,
        items=[MaterialRequestItem.model_validate(item) for item in items_raw],
        total_qty=Decimal(str(total_qty)),
        estimated_total_amount=Decimal(str(estimated_total_amount)),
        suggested_supplier_id=request_supplier["supplier_id"],
        suggested_supplier_name=request_supplier["supplier_name"],
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(material_request)

    return {"id": doc_id, "message": "자재요청이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("material_request:read"))])
def 자재요청_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """자재요청 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("material_request:read"))])
def 자재요청_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자재요청 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("material_request:write"))])
def 자재요청_수정(
    doc_id: str,
    body: MaterialRequestUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """자재요청을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        update_data["items"], estimated_total_amount, request_supplier = _enrich_items(
            user.tenant_id,
            update_data["items"],
        )
        update_data["total_qty"] = _calculate_total_qty(update_data["items"])
        update_data["estimated_total_amount"] = estimated_total_amount
        update_data["suggested_supplier_id"] = request_supplier["supplier_id"]
        update_data["suggested_supplier_name"] = request_supplier["supplier_name"]

    merged_budget_limit = update_data.get("budget_limit", doc.get("budget_limit", 0))
    update_data["budget_status"] = _resolve_budget_status(
        {
            "budget_limit": merged_budget_limit,
            "estimated_total_amount": update_data.get(
                "estimated_total_amount",
                doc.get("estimated_total_amount", 0),
            ),
        },
    )
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "자재요청이 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("material_request:submit"))]
)
def 자재요청_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자재요청을 제출한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    budget_status = _resolve_budget_status(doc, enforce=True)
    request_type = str(doc.get("request_type", "purchase"))
    estimated_total_amount = _serialize_decimal(doc.get("estimated_total_amount", 0))
    primary_item_group = _pick_primary_item_group(doc.get("items", []))

    if request_type == "purchase" and primary_item_group and estimated_total_amount > 0:
        approval = BuyerApprovalService(user.tenant_id).get_approver(
            primary_item_group,
            estimated_total_amount,
        )
        repo.update_by_id(
            doc_id,
            {
                "docstatus": DocStatus.SUBMITTED,
                "approval_status": "pending",
                "required_approver": approval["approver"],
                "approval_matrix_id": approval["matrix_id"],
                "approval_requested_by": user.sub,
                "budget_status": budget_status,
                "updated_by": user.sub,
            },
        )
        return {
            "id": doc_id,
            "message": "자재요청이 제출되었고 승인 대기 상태로 전환되었습니다",
            "approval_status": "pending",
            "required_approver": approval["approver"],
        }

    repo.update_with_event(
        doc_id,
        {
            "docstatus": DocStatus.SUBMITTED,
            "approval_status": "not_required",
            "budget_status": budget_status,
            "updated_by": user.sub,
        },
        event_type=EventType.MATERIAL_REQUEST_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {
        "id": doc_id,
        "message": "자재요청이 제출되었습니다",
        "approval_status": "not_required",
    }


def _assert_pending_approval(doc: dict[str, Any], user: CurrentUserDep) -> None:
    """승인/반려 가능 상태와 결재자 권한을 검증한다."""
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 승인 또는 반려할 수 있습니다")
    if doc.get("approval_status") != "pending":
        raise_bad_request("승인 대기 상태의 자재요청만 처리할 수 있습니다")
    required_approver = str(doc.get("required_approver", "")).strip()
    if required_approver and required_approver != user.sub:
        raise_unprocessable("ERR-BUY-042", "지정된 결재자만 이 자재요청을 처리할 수 있습니다")


@router.post(
    "/{doc_id}/approve",
    dependencies=[Depends(require_permission("material_request:approve"))],
)
def 자재요청_승인(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """승인 대기 중인 자재요청을 승인하고 구매주문 생성 이벤트를 발행한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    _assert_pending_approval(doc, user)

    repo.update_with_event(
        doc_id,
        {
            "approval_status": "approved",
            "approved_by": user.sub,
            "approved_at": datetime.now(tz=UTC),
            "updated_by": user.sub,
        },
        event_type=EventType.MATERIAL_REQUEST_SUBMITTED,
        event_data={"doc_id": doc_id, "approved_by": user.sub},
        triggered_by=user.sub,
    )
    return {
        "id": doc_id,
        "message": "자재요청이 승인되었습니다",
        "approval_status": "approved",
    }


@router.post(
    "/{doc_id}/reject",
    dependencies=[Depends(require_permission("material_request:reject"))],
)
def 자재요청_반려(doc_id: str, user: CurrentUserDep, reason: str = "") -> dict[str, Any]:
    """승인 대기 중인 자재요청을 반려한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    _assert_pending_approval(doc, user)

    repo.update_by_id(
        doc_id,
        {
            "approval_status": "rejected",
            "rejected_by": user.sub,
            "rejected_reason": reason,
            "updated_by": user.sub,
        },
    )
    return {
        "id": doc_id,
        "message": "자재요청이 반려되었습니다",
        "approval_status": "rejected",
    }


@router.post(
    "/{doc_id}/create-rfq",
    status_code=201,
    dependencies=[Depends(require_permission("request_for_quotation:create"))],
)
def 자재요청에서_RFQ_생성(
    doc_id: str,
    body: MaterialRequestCreateRFQ,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """구매 자재요청에서 직접 RFQ를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    if str(doc.get("request_type", "purchase")) != "purchase":
        raise_unprocessable("ERR-BUY-043", "구매 유형의 자재요청에서만 RFQ를 생성할 수 있습니다")
    if doc.get("docstatus", 0) == DocStatus.CANCELLED:
        raise_bad_request("취소된 자재요청에서는 RFQ를 생성할 수 없습니다")

    result = PurchaseProcessService(user.tenant_id).create_rfq_from_mr(
        doc_id,
        suppliers=body.suppliers,
        transaction_date=body.transaction_date,
    )
    return {
        "id": result["rfq_id"],
        "message": "자재요청에서 견적요청이 생성되었습니다",
        "material_request_id": doc_id,
        "supplier_count": result["supplier_count"],
        "item_count": result["item_count"],
    }


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("material_request:cancel"))]
)
def 자재요청_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자재요청을 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "자재요청이 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("material_request:delete"))],
)
def 자재요청_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """자재요청을 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자재요청을 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 삭제할 수 있습니다")

    repo.delete_by_id(doc_id)
