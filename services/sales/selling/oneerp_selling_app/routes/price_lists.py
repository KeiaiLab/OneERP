"""가격표(PriceList) 커스텀 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_selling_app.models.price_list import PriceList, PriceListCreate, PriceListUpdate
from oneerp_selling_app.services.price_list_service import PriceListService

router = APIRouter(prefix="/api/v1/price-lists", tags=["가격표"])

_COLLECTION = "price_lists"
_CUSTOMER_GROUP_COLLECTION = "customer_groups"
_QUOTATION_COLLECTION = "quotations"
_POS_PROFILE_COLLECTION = "pos_profiles"
_PREFIX = "PLT"
_NOT_FOUND_MESSAGE = "가격표를 찾을 수 없습니다"


def _get_price_list_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_customer_group_repo(tenant_id: str) -> Repository:
    return Repository(_CUSTOMER_GROUP_COLLECTION, tenant_id=tenant_id)


def _get_quotation_repo(tenant_id: str) -> Repository:
    return Repository(_QUOTATION_COLLECTION, tenant_id=tenant_id)


def _get_pos_profile_repo(tenant_id: str) -> Repository:
    return Repository(_POS_PROFILE_COLLECTION, tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return date.fromisoformat(value)
    return None


def _get_usage_summary(tenant_id: str, document: dict[str, Any]) -> dict[str, Any]:
    doc_id = str(document.get("_id") or "")
    customer_groups = _get_customer_group_repo(tenant_id).find_many(
        {"default_price_list": doc_id}, limit=1000
    )
    quotations = _get_quotation_repo(tenant_id).find_many({"price_list_id": doc_id}, limit=1000)
    pos_profiles = _get_pos_profile_repo(tenant_id).find_many({"price_list": doc_id}, limit=1000)
    items = list(document.get("items") or [])
    return {
        "customer_group_count": len(customer_groups),
        "quotation_count": len(quotations),
        "active_quotation_count": sum(
            1
            for quotation in quotations
            if quotation.get("docstatus") in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}
        ),
        "pos_profile_count": len(pos_profiles),
        "total_item_count": len(items),
        "tiered_item_count": sum(1 for item in items if _to_decimal(item.get("min_qty", 0)) > 1),
    }


def _get_rate_summary(document: dict[str, Any]) -> dict[str, Any]:
    items = list(document.get("items") or [])
    prices = [_to_decimal(item.get("price", 0)) for item in items]
    return {
        "currency": document.get("currency", "KRW"),
        "item_count": len(items),
        "tiered_item_count": sum(1 for item in items if _to_decimal(item.get("min_qty", 0)) > 1),
        "min_price": float(min(prices)) if prices else 0.0,
        "max_price": float(max(prices)) if prices else 0.0,
    }


def _status_badge(
    document: dict[str, Any], usage_summary: dict[str, Any], *, as_of_date: date | None = None
) -> str:
    if not document.get("is_active", True):
        return "inactive"
    today = as_of_date or datetime.now(UTC).date()
    valid_to = _normalize_date(document.get("valid_to"))
    if valid_to and valid_to < today:
        return "expired"
    if valid_to and valid_to <= today + timedelta(days=7):
        return "expiring_soon"
    if usage_summary["quotation_count"] > 0 or usage_summary["pos_profile_count"] > 0:
        return "active_in_use"
    if usage_summary["customer_group_count"] > 0:
        return "active_customer_group"
    return "active_ready"


def _recommended_action(status_badge: str) -> str:
    if status_badge in {"expired", "expiring_soon"}:
        return "review_validity"
    if status_badge == "active_in_use":
        return "review_quote_usage"
    if status_badge == "active_customer_group":
        return "verify_catalog_assignment"
    if status_badge == "inactive":
        return "reactivate_price_list"
    return "preview_catalog"


def _available_actions(status_badge: str, usage_summary: dict[str, Any]) -> list[str]:
    actions = ["edit", "open_catalog_preview"]
    if usage_summary["customer_group_count"] > 0:
        actions.append("open_customer_groups")
    if usage_summary["quotation_count"] > 0:
        actions.append("open_quotations")
    if usage_summary["pos_profile_count"] > 0:
        actions.append("open_pos_profiles")
    if status_badge == "inactive":
        actions.append("reactivate")
    return actions


def _serialize(document: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    usage_summary = _get_usage_summary(tenant_id, document)
    rate_summary = _get_rate_summary(document)
    status_badge = _status_badge(document, usage_summary)
    return {
        **document,
        "id": document.get("_id"),
        "_id": document.get("_id"),
        "item_count": len(document.get("items", [])),
        "usage_summary": usage_summary,
        "rate_summary": rate_summary,
        "status_badge": status_badge,
        "recommended_action": _recommended_action(status_badge),
        "available_actions": _available_actions(status_badge, usage_summary),
    }


def _filter_documents(
    documents: list[dict[str, Any]],
    *,
    currency: str | None = None,
    customer_group: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    filtered = []
    for document in documents:
        if currency and document.get("currency") != currency:
            continue
        if customer_group and document.get("customer_group") != customer_group:
            continue
        if is_active is not None and bool(document.get("is_active", True)) is not is_active:
            continue
        filtered.append(document)
    return sorted(
        filtered,
        key=lambda document: (
            not bool(document.get("is_active", True)),
            document.get("customer_group") or "",
            document.get("currency") or "",
            document.get("price_list_name") or "",
        ),
    )


def _list_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "active_count": sum(1 for document in documents if document["status_badge"] != "inactive"),
        "inactive_count": sum(
            1 for document in documents if document["status_badge"] == "inactive"
        ),
        "expiring_soon_count": sum(
            1 for document in documents if document["status_badge"] == "expiring_soon"
        ),
        "customer_group_bound_count": sum(
            1 for document in documents if document["usage_summary"]["customer_group_count"] > 0
        ),
        "quotation_usage_count": sum(
            1 for document in documents if document["usage_summary"]["quotation_count"] > 0
        ),
        "total_item_count": sum(
            document["usage_summary"]["total_item_count"] for document in documents
        ),
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("price_list:create"))])
def create_price_list(body: PriceListCreate, user: CurrentUserDep) -> dict[str, Any]:
    """가격표를 생성한다."""
    repo = _get_price_list_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    payload = body.model_dump(mode="json")
    document = PriceList(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **body.model_dump(),
    )
    repo.insert(document)
    return {"_id": doc_id, "id": doc_id, **payload}


@router.get("", dependencies=[Depends(require_permission("price_list:read"))])
def list_price_lists(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    currency: str | None = None,
    customer_group: str | None = None,
    is_active: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """가격표 목록을 워크벤치 요약과 함께 조회한다."""
    repo = _get_price_list_repo(user.tenant_id)
    base_documents = _filter_documents(
        repo.find_many(limit=1000, sort=[("price_list_name", 1)]),
        currency=currency,
        customer_group=customer_group,
        is_active=is_active,
    )
    serialized = [_serialize(document, tenant_id=user.tenant_id) for document in base_documents]
    filtered = [
        document
        for document in serialized
        if not status_badge or document["status_badge"] == status_badge
    ]
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _list_summary(serialized),
    }


@router.get("/catalog", dependencies=[Depends(require_permission("price_list:read"))])
def get_price_list_catalog(
    user: CurrentUserDep,
    customer_group: str | None = None,
    currency: str | None = None,
    transaction_date: date | None = None,
) -> dict[str, Any]:
    """고객군/통화/거래일 기준으로 적용 가능한 가격표 카탈로그를 조회한다."""
    service = PriceListService(user.tenant_id)
    documents = service.catalog(
        customer_group=customer_group,
        currency=currency,
        transaction_date=transaction_date,
    )
    return {
        "data": [_serialize(document, tenant_id=user.tenant_id) for document in documents],
        "total": len(documents),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("price_list:read"))])
def get_price_list(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """가격표 단건을 조회한다."""
    document = _get_price_list_repo(user.tenant_id).find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    return _serialize(document, tenant_id=user.tenant_id)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("price_list:write"))])
def update_price_list(
    doc_id: str,
    body: PriceListUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """가격표를 수정한다."""
    repo = _get_price_list_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    update_data = body.model_dump(exclude_none=True)
    if update_data:
        update_data["updated_by"] = user.sub
        repo.update_by_id(doc_id, update_data)
    refreshed = repo.find_by_id(doc_id) or {**document, **update_data}
    refreshed = cast("dict[str, Any]", refreshed)
    return _serialize(refreshed, tenant_id=user.tenant_id)


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("price_list:delete"))],
)
def delete_price_list(doc_id: str, user: CurrentUserDep) -> None:
    """다른 문서에서 사용 중인 가격표 삭제를 차단한다."""
    repo = _get_price_list_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    if _get_customer_group_repo(user.tenant_id).find_many({"default_price_list": doc_id}, limit=1):
        raise_unprocessable("ERR-SELL-044", "고객그룹에서 사용하는 가격표는 삭제할 수 없습니다")
    if _get_quotation_repo(user.tenant_id).find_many({"price_list_id": doc_id}, limit=1):
        raise_unprocessable("ERR-SELL-044", "견적에서 사용하는 가격표는 삭제할 수 없습니다")
    if _get_pos_profile_repo(user.tenant_id).find_many({"price_list": doc_id}, limit=1):
        raise_unprocessable("ERR-SELL-044", "POS 프로필에서 사용하는 가격표는 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
