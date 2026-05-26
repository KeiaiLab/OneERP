"""입고전표(PurchaseReceipt) 비즈니스 로직 — route/Repository 경계 계층.

기존 route의 동작을 경계 이동만 수행한다. 입고 검수/재고 차감 로직 확장은 별도 작업.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.events.schemas import EventType
from oneerp_core.repository import Repository

_COLLECTION = "purchase_receipts"

type SortSpec = list[tuple[str, int]] | None
type DocumentList = list[dict[str, Any]]


class PurchaseReceiptService:
    """입고전표 유스케이스 계층."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._repo: Repository = Repository(_COLLECTION, tenant_id=tenant_id)

    def create(self, doc_id: str, payload: dict[str, Any], *, created_by: str) -> str:
        """입고전표를 생성한다. payload는 route에서 계산된 총계 포함 완성본."""
        doc_data = {
            "_id": doc_id,
            "tenant_id": self._tenant_id,
            "docstatus": DocStatus.DRAFT,
            "created_by": created_by,
            "updated_by": created_by,
            **payload,
        }
        self._repo.insert(doc_data)
        return doc_id

    def get(self, doc_id: str) -> dict[str, Any] | None:
        return self._repo.find_by_id(doc_id)

    def list(self, *, skip: int, limit: int, sort: SortSpec = None) -> DocumentList:
        return self._repo.find_many(skip=skip, limit=limit, sort=sort)

    def count(self) -> int:
        return self._repo.count()

    def submit(self, doc_id: str, *, triggered_by: str) -> None:
        """입고전표를 제출하고 재고 원장이 수신할 이벤트를 발행한다."""
        self._repo.submit_with_event(
            doc_id,
            event_type=EventType.PURCHASE_RECEIPT_SUBMITTED,
            event_data={"doc_id": doc_id},
            triggered_by=triggered_by,
        )
