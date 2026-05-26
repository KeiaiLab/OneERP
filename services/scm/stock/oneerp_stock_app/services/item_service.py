"""품목(Item) 비즈니스 로직 — route/Repository 사이의 경계 계층.

route는 이 서비스만 호출한다. Repository 직접 인스턴스화는 여기서만 발생한다.
경계 이동만 허용하므로 기존 route의 쿼리 동작을 그대로 노출한다.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.repository import Repository

from oneerp_stock_app.dto import ItemCreate, ItemUpdate  # noqa: TC001
from oneerp_stock_app.models.item import Item

_COLLECTION = "items"
_VARIANT_COLLECTION = "item_variants"
_PRICE_COLLECTION = "item_prices"
_STOCK_BIN_COLLECTION = "stock_bins"
_STOCK_LEDGER_COLLECTION = "stock_ledger_entries"

type SortSpec = list[tuple[str, int]] | None
type DocumentList = list[dict[str, Any]]


class ItemService:
    """품목 유스케이스 — 라우트가 필요로 하는 모든 저장소 접근을 캡슐화한다."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._items: Repository = Repository(_COLLECTION, tenant_id=tenant_id)
        self._variants: Repository = Repository(_VARIANT_COLLECTION, tenant_id=tenant_id)
        self._prices: Repository = Repository(_PRICE_COLLECTION, tenant_id=tenant_id)
        self._bins: Repository = Repository(_STOCK_BIN_COLLECTION, tenant_id=tenant_id)
        self._ledger: Repository = Repository(_STOCK_LEDGER_COLLECTION, tenant_id=tenant_id)

    # --- 품목 CRUD ---

    def find_existing(self, item_code: str) -> dict[str, Any] | None:
        """같은 테넌트 내 기존 품목을 조회한다."""
        existing = self._items.find_by_id(item_code)
        if existing:
            return existing
        for document in self._items.find_many({"item_code": item_code}, limit=5):
            return document
        return None

    def create(self, item_code: str, dto: ItemCreate) -> str:
        """품목을 생성한다."""
        item = Item(
            item_code=item_code,
            tenant_id=self._tenant_id,
            **dto.model_dump(exclude={"item_code"}),
        )
        item.id = item_code
        self._items.insert(item)
        return item_code

    def get(self, item_code: str) -> dict[str, Any] | None:
        return self._items.find_by_id(item_code)

    def list(
        self,
        query: dict[str, Any],
        *,
        skip: int,
        limit: int,
        sort: SortSpec = None,
    ) -> DocumentList:
        return self._items.find_many(query, skip=skip, limit=limit, sort=sort)

    def count(self, query: dict[str, Any]) -> int:
        return self._items.count(query)

    def update(self, item_code: str, patch: dict[str, Any]) -> None:
        self._items.update_by_id(item_code, patch)

    def delete(self, item_code: str) -> None:
        self._items.delete_by_id(item_code)

    # --- 연관 데이터 조회 (워크벤치 요약에 필요) ---

    def list_variants(self, item_code: str, *, limit: int = 200) -> DocumentList:
        return self._variants.find_many({"variant_of": item_code}, limit=limit)

    def list_prices(self, item_code: str, *, limit: int = 200) -> DocumentList:
        return self._prices.find_many({"item_code": item_code}, limit=limit)

    def list_bins(self, item_code: str, *, limit: int = 200) -> DocumentList:
        return self._bins.find_many({"item_code": item_code}, limit=limit)

    def list_ledger(self, item_code: str, *, limit: int = 50) -> DocumentList:
        return self._ledger.find_many(
            {"item_code": item_code},
            limit=limit,
            sort=[("created_at", -1)],
        )

    def has_variants(self, item_code: str) -> bool:
        return bool(self._variants.find_many({"variant_of": item_code}, limit=1))

    def has_prices(self, item_code: str) -> bool:
        return bool(self._prices.find_many({"item_code": item_code}, limit=1))

    def has_stock_history(self, item_code: str) -> bool:
        return bool(self._ledger.find_many({"item_code": item_code}, limit=1))

    # --- 편의 메서드 ---

    def apply_update(self, item_code: str, dto: ItemUpdate) -> dict[str, Any]:
        """ItemUpdate DTO를 반영한다. 빈 패치는 예외 없이 반환만."""
        patch = dto.model_dump(exclude_none=True)
        if patch:
            self._items.update_by_id(item_code, patch)
        return patch
