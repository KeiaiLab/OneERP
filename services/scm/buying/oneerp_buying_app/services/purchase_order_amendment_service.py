"""발주 변경 관리 서비스 — 제출된 PO의 수량/단가/일자 변경 이력 추적.

BR-BUY-NEW-022: 제출된 PurchaseOrder의 amendment를 기록하고 차액(delta)을 계산.

참조:
- ERPNext Purchase Order "Amend" 기능: 취소 후 새 리비전 생성
- Cornell Purchase Order Amendment (POA) e-doc: 기존 PO를 기반으로 변경 문서 생성
- P2P 모범사례: 3-way matching, audit trail, cumulative delta

원칙:
- Draft(docstatus=0)는 일반 update_item으로 수정 (amendment 불필요)
- Submitted(docstatus=1)만 amendment 가능
- Cancelled(docstatus=2)는 amendment 금지
- 각 amendment는 POAM 문서로 영속화 (amendment_no 자동 증가)
- 원본 PO의 items/grand_total은 갱신, 이력은 POAM에 보존
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PurchaseOrderAmendmentService:
    """발주 변경 관리 비즈니스 로직.

    제출된 PurchaseOrder의 수량/단가 변경을 이력으로 추적하고
    원본 PO의 grand_total을 재계산한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._po_repo = Repository("purchase_orders", tenant_id=tenant_id)
        self._amend_repo = Repository("purchase_order_amendments", tenant_id=tenant_id)

    def amend_order(
        self,
        *,
        po_id: str,
        changes: list[dict[str, Any]],
        reason: str,
    ) -> dict[str, Any]:
        """제출된 PO의 품목 수량/단가를 변경하고 amendment 이력을 생성한다.

        Args:
            po_id: PurchaseOrder ID (docstatus=1이어야 함)
            changes: 변경 사항 목록
                [{"item_code": "ITEM-001", "new_qty": 120}, ...]
                [{"item_code": "ITEM-001", "new_rate": 5500}, ...]
                (new_qty / new_rate 중 하나 이상 지정)
            reason: 변경 사유 (감사 로그용)

        Returns:
            {amendment_id, po_id, amendment_no, reason,
             old_grand_total, new_grand_total, delta}

        Raises:
            OneERPError: PO 미존재(404), docstatus≠1(422), 품목 미매칭(422),
                         빈 changes(400)
        """
        if not changes:
            raise_bad_request("변경 사항이 비어 있습니다")

        po = self._po_repo.find_by_id(po_id)
        if not po:
            raise_not_found(f"발주서 '{po_id}'를 찾을 수 없습니다")

        docstatus = int(po.get("docstatus", 0))
        if docstatus == 0:
            raise_unprocessable(
                "ERR-BUY-035",
                "Draft 발주는 일반 수정 API를 사용하세요 (amendment는 제출된 발주만 가능)",
            )
        if docstatus == 2:
            raise_unprocessable(
                "ERR-BUY-036",
                "취소된 발주는 변경할 수 없습니다",
            )

        # 기존 품목 매핑
        items = list(po.get("items", []))
        items_by_code: dict[str, dict[str, Any]] = {
            str(it.get("item_code", "")): dict(it) for it in items
        }

        # 변경 적용 + 차액 계산
        item_changes: list[dict[str, Any]] = []
        amount_delta = 0.0
        for change in changes:
            item_code = str(change.get("item_code", ""))
            if item_code not in items_by_code:
                raise_unprocessable(
                    "ERR-BUY-037",
                    f"품목 '{item_code}'이 발주서에 없습니다",
                )

            item = items_by_code[item_code]
            old_qty = float(item.get("qty", 0))
            old_rate = float(item.get("rate", 0))
            old_amount = round(old_qty * old_rate, 2)

            new_qty = float(change.get("new_qty", old_qty))
            new_rate = float(change.get("new_rate", old_rate))
            new_amount = round(new_qty * new_rate, 2)

            delta = round(new_amount - old_amount, 2)
            amount_delta = round(amount_delta + delta, 2)

            item["qty"] = new_qty
            item["rate"] = new_rate
            item["amount"] = new_amount
            items_by_code[item_code] = item

            item_changes.append(
                {
                    "item_code": item_code,
                    "old_qty": old_qty,
                    "new_qty": new_qty,
                    "old_rate": old_rate,
                    "new_rate": new_rate,
                    "old_amount": old_amount,
                    "new_amount": new_amount,
                    "delta": delta,
                }
            )

        old_grand_total = float(po.get("grand_total", 0))
        new_grand_total = round(old_grand_total + amount_delta, 2)

        # 기존 amendment 건수 기반으로 amendment_no 산출
        prior_amendments = self._amend_repo.find_many({"po_id": po_id}, limit=1000)
        amendment_no = len(prior_amendments) + 1

        # 원본 PO 갱신 (items/grand_total)
        updated_items = [items_by_code[str(it.get("item_code", ""))] for it in items]
        self._po_repo.update_by_id(
            po_id,
            {
                "items": updated_items,
                "grand_total": new_grand_total,
                "total": new_grand_total,
            },
        )

        # amendment 문서 생성
        amendment_id = generate_name("POAM", tenant_id=self._tenant_id)
        amend_doc = {
            "_id": amendment_id,
            "po_id": po_id,
            "amendment_no": amendment_no,
            "reason": reason,
            "old_grand_total": old_grand_total,
            "new_grand_total": new_grand_total,
            "delta": {
                "amount_delta": amount_delta,
                "item_changes": item_changes,
            },
            "created_at": datetime.now(tz=UTC).isoformat(),
            "tenant_id": self._tenant_id,
        }
        self._amend_repo.insert(amend_doc)

        logger.info(
            "발주 변경: PO=%s, 변경=%d건, delta=%.2f, amendment_no=%d",
            po_id,
            len(item_changes),
            amount_delta,
            amendment_no,
        )

        return {
            "amendment_id": amendment_id,
            "po_id": po_id,
            "amendment_no": amendment_no,
            "reason": reason,
            "old_grand_total": old_grand_total,
            "new_grand_total": new_grand_total,
            "delta": {
                "amount_delta": amount_delta,
                "item_changes": item_changes,
            },
        }

    def get_amendment_history(self, po_id: str) -> list[dict[str, Any]]:
        """특정 PO의 amendment 이력을 amendment_no 오름차순으로 조회한다.

        Args:
            po_id: PurchaseOrder ID

        Returns:
            amendment 문서 목록 (amendment_no asc)
        """
        amendments = self._amend_repo.find_many({"po_id": po_id}, limit=1000)
        amendments.sort(key=lambda a: int(a.get("amendment_no", 0)))

        logger.info("발주 변경 이력 조회: PO=%s, 이력=%d건", po_id, len(amendments))
        return amendments
