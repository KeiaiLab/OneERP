"""품목(Item) CRUD 라우터.

OE002: Repository는 ItemService 안에서만 사용한다.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from oneerp_stock_app.dto import ItemCreate, ItemUpdate
from oneerp_stock_app.services.item_service import ItemService

router = APIRouter(prefix="/api/v1/items", tags=["품목"])

_ITEM_CODE_SANITIZER = re.compile(r"[^A-Z0-9-]+")


def get_service(user: CurrentUserDep) -> ItemService:
    """요청 테넌트에 바인딩된 ItemService를 생성한다."""
    return ItemService(user.tenant_id)


ItemServiceDep = Annotated[ItemService, Depends(get_service)]


def _normalize_item_code(raw_code: str) -> str:
    """사용자 입력 품목 코드를 저장용 포맷으로 정규화한다."""
    normalized = _ITEM_CODE_SANITIZER.sub("-", raw_code.upper()).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


def _to_decimal(value: Any) -> Decimal:
    """임의 숫자 값을 Decimal로 정규화한다."""
    if isinstance(value, Decimal):
        return value
    if value in (None, ""):
        return Decimal(0)
    try:
        return Decimal(str(value))
    except InvalidOperation, TypeError, ValueError:
        return Decimal(0)


def _to_float(value: Any) -> float:
    """API 응답 직렬화를 위해 Decimal 값을 float로 변환한다."""
    return float(_to_decimal(value))


def _coerce_datetime(value: Any) -> datetime | None:
    """문서 날짜/문자열을 UTC datetime으로 변환한다."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _serialize_date(value: Any) -> str:
    """날짜 값을 ISO 날짜 문자열로 직렬화한다."""
    parsed = _coerce_datetime(value)
    if parsed is None:
        return ""
    return parsed.date().isoformat()


def _build_variant_summary(
    service: ItemService, item_code: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """품목 변형 요약을 계산한다."""
    variants = service.list_variants(item_code)
    return {
        "variant_count": len(variants),
        "variant_item_codes": [str(variant.get("item_code", "")) for variant in variants],
    }, variants


def _build_pricing_summary(
    service: ItemService, item_code: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """품목 가격 요약을 계산한다."""
    prices = service.list_prices(item_code)
    price_values = [_to_decimal(price.get("price")) for price in prices]
    currencies = {
        str(price.get("currency", "")).strip() for price in prices if price.get("currency")
    }
    return {
        "price_count": len(prices),
        "price_list_count": len({str(price.get("price_list", "")).strip() for price in prices}),
        "min_price": _to_float(min(price_values)) if price_values else 0.0,
        "max_price": _to_float(max(price_values)) if price_values else 0.0,
        "currency": sorted(currencies)[0] if len(currencies) == 1 else "",
    }, prices


def _build_inventory_summary(
    service: ItemService, item: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """현재 재고 잔고와 최근 이동 정보를 요약한다."""
    item_code = str(item.get("item_code") or item.get("_id") or "")
    bins = service.list_bins(item_code)
    ledgers = service.list_ledger(item_code)
    reorder_level = _to_decimal(item.get("reorder_level"))
    current_qty = sum(_to_decimal(bin_doc.get("current_qty")) for bin_doc in bins)
    stock_value = sum(_to_decimal(bin_doc.get("stock_value")) for bin_doc in bins)
    return {
        "warehouse_count": len(
            {str(bin_doc.get("warehouse", "")) for bin_doc in bins if bin_doc.get("warehouse")}
        ),
        "current_qty": _to_float(current_qty),
        "stock_value": _to_float(stock_value),
        "reorder_level": _to_float(reorder_level),
        "is_below_reorder": bool(item.get("is_stock_item", True))
        and reorder_level > 0
        and current_qty < reorder_level,
        "last_movement_date": _serialize_date(
            ledgers[0].get("posting_date") if ledgers else item.get("updated_at")
        ),
    }, ledgers


def _status_badge_for(
    item: dict[str, Any],
    inventory_summary: dict[str, Any],
    variant_summary: dict[str, Any],
    pricing_summary: dict[str, Any],
) -> str:
    """품목 상태 배지를 계산한다."""
    if not item.get("is_stock_item", True):
        return "service_item"
    if inventory_summary["is_below_reorder"]:
        return "reorder_due"
    if item.get("has_batch_no") or item.get("has_serial_no"):
        return "tracking_required"
    if variant_summary["variant_count"] > 0:
        return "variant_template"
    if pricing_summary["price_count"] == 0:
        return "price_missing"
    return "inventory_ready"


def _recommended_action_for(
    status_badge: str,
    pricing_summary: dict[str, Any],
) -> str:
    """다음 권장 액션을 계산한다."""
    if status_badge == "reorder_due":
        return "review_replenishment"
    if pricing_summary["price_count"] == 0:
        return "add_item_price"
    if status_badge == "variant_template":
        return "review_variant_matrix"
    if status_badge == "tracking_required":
        return "verify_tracking_policy"
    return "review_item_availability"


def _available_actions_for(
    item: dict[str, Any],
    inventory_summary: dict[str, Any],
    *,
    has_linked_records: bool,
) -> list[str]:
    """품목 상세/목록에서 노출할 액션 목록을 계산한다."""
    actions = ["edit", "manage_variants", "manage_prices"]
    if item.get("is_stock_item", True):
        actions.append("view_stock_balance")
    if inventory_summary["last_movement_date"]:
        actions.append("open_stock_ledger")
    if not has_linked_records:
        actions.append("delete")
    return actions


def _decorate_item(service: ItemService, item: dict[str, Any]) -> dict[str, Any]:
    """품목 문서를 워크벤치 응답으로 확장한다."""
    item_code = str(item.get("item_code") or item.get("_id") or "")
    inventory_summary, ledgers = _build_inventory_summary(service, item)
    variant_summary, variants = _build_variant_summary(service, item_code)
    pricing_summary, prices = _build_pricing_summary(service, item_code)
    status_badge = _status_badge_for(item, inventory_summary, variant_summary, pricing_summary)
    has_linked_records = bool(variants or prices or ledgers)
    return {
        **item,
        "inventory_summary": inventory_summary,
        "variant_summary": variant_summary,
        "pricing_summary": pricing_summary,
        "status_badge": status_badge,
        "recommended_action": _recommended_action_for(status_badge, pricing_summary),
        "available_actions": _available_actions_for(
            item,
            inventory_summary,
            has_linked_records=has_linked_records,
        ),
    }


def _build_listing_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    """품목 워크벤치 상단 요약을 계산한다."""
    return {
        "total_item_count": len(items),
        "stock_item_count": sum(1 for item in items if item.get("is_stock_item", True)),
        "service_item_count": sum(1 for item in items if not item.get("is_stock_item", True)),
        "reorder_due_count": sum(1 for item in items if item.get("status_badge") == "reorder_due"),
        "variant_template_count": sum(
            1 for item in items if item.get("variant_summary", {}).get("variant_count", 0) > 0
        ),
        "tracked_item_count": sum(
            1 for item in items if item.get("has_batch_no") or item.get("has_serial_no")
        ),
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("item:create"))])
def create_item(body: ItemCreate, user: CurrentUserDep, service: ItemServiceDep) -> dict:
    """품목을 생성한다."""
    requested_item_code = _normalize_item_code(body.item_code or "")
    item_code = requested_item_code or generate_name("ITEM", tenant_id=user.tenant_id)
    if service.find_existing(item_code):
        raise OneERPError(409, "이미 같은 품목 코드가 존재합니다", detail=f"item_code={item_code}")
    service.create(item_code, body)
    return {"id": item_code, "item_code": item_code, "message": "품목이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("item:read"))])
def list_items(
    service: ItemServiceDep,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    item_group: str | None = Query(None, description="품목 그룹 필터"),
    status_badge: str | None = Query(None, description="품목 상태 배지 필터"),
    is_stock_item_filter: str | None = Query(
        None,
        alias="is_stock_item",
        description="재고 품목 여부 필터(true/false)",
    ),
) -> dict:
    """품목 목록을 조회한다 (워크벤치 요약 + 상태 필터)."""
    query: dict = {}
    if item_group:
        query["item_group"] = item_group
    if is_stock_item_filter is not None:
        query["is_stock_item"] = is_stock_item_filter.lower() in {"1", "true", "yes", "y"}

    skip = (page - 1) * page_size
    if status_badge:
        raw_items = service.list(query, skip=0, limit=200, sort=[("created_at", -1)])
    else:
        raw_items = service.list(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    items = [_decorate_item(service, item) for item in raw_items]
    if status_badge:
        items = [item for item in items if item.get("status_badge") == status_badge]
        total = len(items)
        items = items[skip : skip + page_size]
    else:
        total = service.count(query)
    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_listing_summary(items),
    }


@router.get("/{item_code}/summary", dependencies=[Depends(require_permission("item:read"))])
def get_item_summary(item_code: str, service: ItemServiceDep) -> dict:
    """품목 워크벤치 상세 요약을 조회한다."""
    doc = service.get(item_code)
    if not doc:
        raise OneERPError(404, "품목을 찾을 수 없습니다", detail=f"item_code={item_code}")
    decorated = _decorate_item(service, doc)
    return {
        "item_code": decorated["item_code"],
        "item_name": decorated.get("item_name", ""),
        "item_group": decorated.get("item_group", ""),
        "status_badge": decorated["status_badge"],
        "recommended_action": decorated["recommended_action"],
        "available_actions": decorated["available_actions"],
        "inventory_summary": decorated["inventory_summary"],
        "variant_summary": decorated["variant_summary"],
        "pricing_summary": decorated["pricing_summary"],
    }


@router.get("/{item_code}", dependencies=[Depends(require_permission("item:read"))])
def get_item(item_code: str, service: ItemServiceDep) -> dict:
    """품목을 조회한다."""
    doc = service.get(item_code)
    if not doc:
        raise OneERPError(404, "품목을 찾을 수 없습니다", detail=f"item_code={item_code}")
    return _decorate_item(service, doc)


@router.put("/{item_code}", dependencies=[Depends(require_permission("item:write"))])
def update_item(item_code: str, body: ItemUpdate, service: ItemServiceDep) -> dict:
    """품목을 수정한다."""
    doc = service.get(item_code)
    if not doc:
        raise OneERPError(404, "품목을 찾을 수 없습니다", detail=f"item_code={item_code}")

    patch = body.model_dump(exclude_none=True)
    if not patch:
        raise OneERPError(400, "수정할 내용이 없습니다")

    service.update(item_code, patch)
    return {"item_code": item_code, "message": "품목이 수정되었습니다"}


@router.delete(
    "/{item_code}", status_code=200, dependencies=[Depends(require_permission("item:delete"))]
)
def delete_item(item_code: str, service: ItemServiceDep) -> dict:
    """품목을 삭제한다 (초안 상태만 가능)."""
    doc = service.get(item_code)
    if not doc:
        raise OneERPError(404, "품목을 찾을 수 없습니다", detail=f"item_code={item_code}")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(422, "제출/취소된 문서는 수정할 수 없습니다", detail="ERR-STK-032")

    if (
        service.has_variants(item_code)
        or service.has_prices(item_code)
        or service.has_stock_history(item_code)
    ):
        raise OneERPError(
            422,
            "품목 변형·가격·재고 이력이 연결된 품목은 삭제할 수 없습니다",
            detail="ERR-STK-033",
        )

    service.delete(item_code)
    return {"item_code": item_code, "message": "품목이 삭제되었습니다"}
