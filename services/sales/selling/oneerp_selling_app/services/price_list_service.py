"""가격표 적용 서비스."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

_PRICE_LIST_COLLECTION = "price_lists"


def _normalize_date(value: Any) -> date | None:
    """date/datetime/ISO 문자열을 date로 정규화한다."""
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


class PriceListService:
    """고객군/통화/거래일 기준 가격표 선택과 견적 단가 적용을 담당한다."""

    def __init__(self, tenant_id: str) -> None:
        self._repo = Repository(_PRICE_LIST_COLLECTION, tenant_id=tenant_id)

    def catalog(
        self,
        *,
        customer_group: str | None = None,
        currency: str | None = None,
        transaction_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """적용 가능한 활성 가격표 목록을 반환한다."""
        as_of_date = transaction_date or datetime.now(UTC).date()
        documents = self._repo.find_many(limit=1000, sort=[("price_list_name", 1)])
        catalog: list[dict[str, Any]] = []
        for document in documents:
            if not document.get("is_active", True):
                continue
            if currency and document.get("currency") != currency:
                continue
            if customer_group and document.get("customer_group") not in {None, "", customer_group}:
                continue
            if not self._is_valid_on(document, as_of_date):
                continue
            catalog.append(
                {
                    **document,
                    "id": document.get("_id"),
                    "item_count": len(document.get("items", [])),
                }
            )
        return catalog

    def apply_price_list(
        self,
        *,
        price_list_id: str,
        items: list[dict[str, Any]],
        transaction_date: date | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """가격표 기준으로 견적 라인의 단가를 재계산한다."""
        document = self._repo.find_by_id(price_list_id)
        if not document:
            raise_not_found("가격표를 찾을 수 없습니다")
        document = cast("dict[str, Any]", document)
        as_of_date = transaction_date or datetime.now(UTC).date()
        if not document.get("is_active", True) or not self._is_valid_on(document, as_of_date):
            raise_unprocessable(
                "ERR-SELL-045", "선택한 거래일에 유효한 활성 가격표만 사용할 수 있습니다"
            )

        priced_items: list[dict[str, Any]] = []
        for item in items:
            qty = Decimal(str(item.get("qty", 0) or 0))
            matched_line = self._match_price_line(
                document.get("items", []), item_code=item["item_code"], qty=qty
            )
            if matched_line is None:
                raise_unprocessable(
                    "ERR-SELL-046",
                    f"가격표에 등록되지 않은 품목입니다: {item['item_code']}",
                )
            rate = Decimal(str(matched_line.get("price", 0) or 0))
            priced_items.append(
                {
                    **item,
                    "rate": rate,
                    "amount": qty * rate,
                }
            )
        return document, priced_items

    @staticmethod
    def _is_valid_on(document: dict[str, Any], as_of_date: date) -> bool:
        valid_from = _normalize_date(document.get("valid_from"))
        valid_to = _normalize_date(document.get("valid_to"))
        if valid_from and as_of_date < valid_from:
            return False
        return not (valid_to and as_of_date > valid_to)

    @staticmethod
    def _match_price_line(
        price_items: list[dict[str, Any]],
        *,
        item_code: str,
        qty: Decimal,
    ) -> dict[str, Any] | None:
        candidates = [
            item
            for item in price_items
            if item.get("item_code") == item_code
            and qty >= Decimal(str(item.get("min_qty", 0) or 0))
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: Decimal(str(item.get("min_qty", 0) or 0)), reverse=True)
        return candidates[0]
