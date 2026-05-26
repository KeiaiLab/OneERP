"""POS 거래(POSTransaction) 서비스 — Route CRUD 위임.

M3 arch-baseline 감소: Route → Service 3층.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class POSTransactionService:
    """POS 거래 CRUD 위임 서비스.

    BR-SELL-011: 제출된 POS 거래는 수정/삭제 차단.
    """

    def __init__(self, tenant_id: str, user_sub: str = "") -> None:
        self._tenant_id = tenant_id
        self._user_sub = user_sub
        self._repo = Repository("pos_transactions", tenant_id=tenant_id)

    def create_from_request(self, body: Any) -> dict[str, Any]:
        """POSTransactionCreate 요청을 받아 거래를 생성한다."""
        from oneerp_selling_app.models.pos_transaction import POSTransaction

        doc_id = generate_name("PTXN", tenant_id=self._tenant_id)
        items_raw = [item.model_dump() for item in body.items]
        items_raw, total = calculate_line_totals(items_raw)

        txn = POSTransaction(
            _id=doc_id,
            tenant_id=self._tenant_id,
            customer_id=body.customer_id,
            customer_name=body.customer_name,
            pos_profile_ref=body.pos_profile_ref,
            posting_date=body.posting_date,
            items=body.items,
            total=total,
            grand_total=total,
            payments=body.payments,
            created_by=self._user_sub,
            updated_by=self._user_sub,
        )
        self._repo.insert(txn)
        return {"id": doc_id, "message": "POS 거래가 생성되었습니다"}

    def list_transactions(self, skip: int, limit: int) -> dict[str, Any]:
        """POS 거래 목록 페이지네이션."""
        docs = self._repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._repo.count()
        return {"data": docs, "total": total}

    def get_transaction(self, doc_id: str) -> dict[str, Any] | None:
        """POS 거래 상세 조회."""
        return self._repo.find_by_id(doc_id)

    def update_transaction(self, doc_id: str, body: Any) -> dict[str, Any]:
        """BR-SELL-011: 제출된 거래 수정 차단."""
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("POS 거래를 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("제출된 POS 거래는 수정/삭제할 수 없습니다")

        update_data = body.model_dump(exclude_none=True)
        if "items" in update_data:
            items_raw = update_data["items"]
            items_raw, total = calculate_line_totals(items_raw)
            update_data["items"] = items_raw
            update_data["total"] = total
            update_data["grand_total"] = total
        update_data["updated_by"] = self._user_sub

        self._repo.update_by_id(doc_id, update_data)
        return {"id": doc_id, "message": "POS 거래가 수정되었습니다"}

    def submit_transaction(self, doc_id: str) -> dict[str, Any]:
        """POS 거래 제출 (초안 → 제출)."""
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("POS 거래를 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("초안 상태에서만 제출할 수 있습니다")

        self._repo.submit_with_event(
            doc_id,
            event_type=EventType.POS_TRANSACTION_SUBMITTED,
            triggered_by=self._user_sub,
        )
        return {"id": doc_id, "message": "POS 거래가 제출되었습니다"}

    def delete_transaction(self, doc_id: str) -> None:
        """BR-SELL-011: 제출된 거래 삭제 차단."""
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("POS 거래를 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("제출된 POS 거래는 수정/삭제할 수 없습니다")

        self._repo.delete_by_id(doc_id)
