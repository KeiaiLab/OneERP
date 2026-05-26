"""Expenses 라우트 전용 애플리케이션 서비스.

라우트는 Repository를 직접 다루지 않고 이 계층을 통해서만
문서 CRUD와 상태 전이를 호출한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

if TYPE_CHECKING:
    from oneerp_core.events.schemas import EventType


class ExpenseRouteService:
    """Expenses CRUD 라우트용 경계 서비스."""

    def __init__(self, collection_name: str, tenant_id: str) -> None:
        self._repo = Repository(collection_name, tenant_id=tenant_id)

    def create(self, document: Any) -> None:
        self._repo.insert(document)

    def list_page(self, *, page: int, page_size: int) -> dict[str, Any]:
        skip = (page - 1) * page_size
        data = self._repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
        total = self._repo.count()
        return {"data": data, "total": total, "page": page, "page_size": page_size}

    def get_or_raise(self, doc_id: str, *, detail: str) -> dict[str, Any]:
        document = self._repo.find_by_id(doc_id)
        if not document:
            raise OneERPError(status_code=404, error="not_found", detail=detail)
        return document

    def update(self, doc_id: str, patch: dict[str, Any]) -> None:
        self._repo.update_by_id(doc_id, patch)

    def delete(self, doc_id: str) -> None:
        self._repo.delete_by_id(doc_id)

    def submit(
        self,
        doc_id: str,
        *,
        event_type: EventType,
        event_data: dict[str, Any] | None = None,
        triggered_by: str,
    ) -> None:
        self._repo.submit_with_event(
            doc_id,
            event_type=event_type,
            event_data=event_data,
            triggered_by=triggered_by,
        )

    def cancel(self, doc_id: str) -> None:
        self._repo.cancel(doc_id)
