"""통화(Currency) CRUD 라우트."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.currency import Currency, CurrencyCreate, CurrencyUpdate

router = APIRouter(prefix="/api/v1/currencies", tags=["통화"])
_COLLECTION = "currencies"
_COMPANY_COLLECTION = "companies"
_SYSTEM_SETTINGS_COLLECTION = "system_settings"
_PREFIX = "CUR"
_DEFAULT_CURRENCY_CODE = "KRW"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_company_repo(tenant_id: str = "") -> Repository:
    """회사 Repository 인스턴스를 반환한다."""
    return Repository(_COMPANY_COLLECTION, tenant_id=tenant_id)


def _get_system_settings_repo(tenant_id: str = "") -> Repository:
    """시스템설정 Repository 인스턴스를 반환한다."""
    return Repository(_SYSTEM_SETTINGS_COLLECTION, tenant_id=tenant_id)


def _normalize_currency_code(raw_code: str) -> str:
    """통화 코드를 ISO 4217 형태로 정규화한다."""
    return raw_code.strip().upper()


def _validate_currency_code(currency_code: str) -> None:
    """통화 코드 형식을 검증한다."""
    if not re.fullmatch(r"[A-Z]{3}", currency_code):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="통화 코드는 ISO 4217 3자리 대문자여야 합니다",
        )


def _find_duplicate_currency(
    repo: Repository,
    currency_code: str,
    *,
    current_id: str | None = None,
) -> dict[str, Any] | None:
    """같은 통화 코드를 사용하는 기존 문서를 찾는다."""
    matches = repo.find_many(query={"currency_code": currency_code}, limit=20)
    for match in matches:
        if match.get("_id") != current_id:
            return match
    return None


def _count_currency_usage(tenant_id: str, currency_code: str) -> int:
    """회사/시스템설정 참조 수를 합산한다."""
    company_repo = _get_company_repo(tenant_id)
    system_settings_repo = _get_system_settings_repo(tenant_id)
    company_usage = company_repo.count({"default_currency": currency_code})
    system_usage = system_settings_repo.count(
        {"setting_key": "default_currency", "setting_value": currency_code}
    )
    return company_usage + system_usage


def _build_catalog_summary(currencies: list[dict[str, Any]]) -> dict[str, Any]:
    """통화 카탈로그 요약을 계산한다."""
    enabled_count = sum(1 for currency in currencies if currency.get("is_enabled", True))
    return {
        "default_currency_code": _DEFAULT_CURRENCY_CODE,
        "enabled_count": enabled_count,
        "disabled_count": len(currencies) - enabled_count,
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("currency:create"))])
async def create_currency(body: CurrencyCreate, user: CurrentUserDep) -> dict:
    """통화를 생성한다."""
    repo = _get_repo(user.tenant_id)
    currency_code = _normalize_currency_code(body.currency_code)
    _validate_currency_code(currency_code)
    if _find_duplicate_currency(repo, currency_code):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="같은 통화 코드는 중복 등록할 수 없습니다",
        )
    doc_id = generate_name(_PREFIX)
    doc = Currency(
        _id=doc_id,
        currency_code=currency_code,
        currency_name=body.currency_name,
        symbol=body.symbol,
        fraction=body.fraction,
        fraction_units=body.fraction_units,
        is_enabled=body.is_enabled,
    )
    repo.insert(doc)
    return {"currency_id": doc_id, "message": "통화가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("currency:read"))])
async def list_currencies(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """통화 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    data = repo.find_many(
        skip=skip, limit=page_size, sort=[("currency_code", 1), ("created_at", -1)]
    )
    total = repo.count()
    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_catalog_summary(data),
    }


@router.get("/catalog", dependencies=[Depends(require_permission("currency:read"))])
async def get_currency_catalog(user: CurrentUserDep) -> dict[str, Any]:
    """활성 통화 카탈로그와 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    all_currencies = repo.find_many(limit=500, sort=[("currency_code", 1), ("created_at", 1)])
    active_currencies = sorted(
        (currency for currency in all_currencies if currency.get("is_enabled", True)),
        key=lambda currency: str(currency.get("currency_code", "")),
    )
    return {
        "data": active_currencies,
        "total": len(active_currencies),
        "summary": _build_catalog_summary(all_currencies),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("currency:read"))])
async def get_currency(doc_id: str, user: CurrentUserDep) -> dict:
    """통화 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="통화를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("currency:write"))])
async def update_currency(doc_id: str, body: CurrencyUpdate, user: CurrentUserDep) -> dict:
    """통화를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="통화를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="bad_request", detail="수정할 내용이 없습니다")

    current_code = _normalize_currency_code(str(doc.get("currency_code", "")))
    if "currency_code" in update_data:
        normalized_code = _normalize_currency_code(str(update_data["currency_code"]))
        _validate_currency_code(normalized_code)
        if _find_duplicate_currency(repo, normalized_code, current_id=doc_id):
            raise OneERPError(
                status_code=422,
                error="validation_error",
                detail="같은 통화 코드는 중복 등록할 수 없습니다",
            )
        update_data["currency_code"] = normalized_code

    next_code = str(update_data.get("currency_code", current_code))
    usage_count = _count_currency_usage(user.tenant_id, current_code)
    if current_code == _DEFAULT_CURRENCY_CODE and (
        next_code != _DEFAULT_CURRENCY_CODE or update_data.get("is_enabled") is False
    ):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="기본 통화 KRW는 비활성화하거나 삭제할 수 없습니다",
        )
    if next_code != current_code and usage_count > 0:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="회사 또는 시스템 설정에서 사용 중인 통화 코드는 변경할 수 없습니다",
        )
    if update_data.get("is_enabled") is False and usage_count > 0:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="회사 또는 시스템 설정에서 사용 중인 통화는 비활성화할 수 없습니다",
        )

    repo.update_by_id(doc_id, update_data)
    return {"message": "통화가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("currency:delete"))])
async def delete_currency(doc_id: str, user: CurrentUserDep) -> dict:
    """통화를 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="통화를 찾을 수 없습니다")
    currency_code = _normalize_currency_code(str(doc.get("currency_code", "")))
    if currency_code == _DEFAULT_CURRENCY_CODE:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="기본 통화 KRW는 비활성화하거나 삭제할 수 없습니다",
        )
    if _count_currency_usage(user.tenant_id, currency_code) > 0:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="회사 또는 시스템 설정에서 사용 중인 통화는 삭제할 수 없습니다",
        )
    repo.delete_by_id(doc_id)
    return {"message": "통화가 삭제되었습니다"}
