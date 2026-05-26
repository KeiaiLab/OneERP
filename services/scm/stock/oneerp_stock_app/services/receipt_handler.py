"""입고 처리 서비스.

구매주문 제출 → 입고전표(PurchaseReceipt) 초안 자동 생성.

NOTE: PurchaseReceipt 모델은 buying 서비스에 정의되어 있으나,
      크로스서비스 의존성을 피하기 위해 BaseDocument 기반으로 직접 생성한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from oneerp_core.document import BaseDocument
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository
from pydantic import Field

logger = logging.getLogger(__name__)


class _PurchaseReceiptDraft(BaseDocument):
    """입고전표 초안 생성용 경량 모델.

    buying 서비스의 PurchaseReceipt 모델과 동일한 필드 구조를 가진다.
    크로스서비스 의존성을 피하기 위해 별도 정의한다.
    """

    supplier: str = ""
    supplier_name: str = ""
    posting_date: datetime | None = None
    items: list[dict] = Field(default_factory=list)
    total_qty: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    warehouse: str = ""
    purchase_order_id: str = ""


class ReceiptHandlerService:
    """입고 처리 서비스.

    구매주문 제출 → 입고전표(PurchaseReceipt) 초안 자동 생성.
    """

    def handle_purchase_order_submitted(self, event_data: dict, tenant_id: str) -> str | None:
        """구매주문 제출 시 입고전표 초안을 생성한다.

        Returns: 생성된 PurchaseReceipt doc_id, 실패 시 None
        """
        doc_id = event_data.get("doc_id")
        if not doc_id:
            logger.warning("이벤트 데이터에 doc_id가 누락되었습니다: %s", event_data)
            return None

        po_repo = Repository("purchase_orders", tenant_id=tenant_id)
        po_doc = po_repo.find_by_id(doc_id)
        if not po_doc:
            logger.warning("구매주문 문서를 찾을 수 없습니다: %s", doc_id)
            return None

        # 입고전표 아이템 매핑
        pr_items = []
        for idx, item in enumerate(po_doc.get("items", []), start=1):
            pr_items.append(
                {
                    "idx": idx,
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "qty": item.get("qty", 0),
                    "rate": item.get("rate", 0),
                    "amount": item.get("amount", 0),
                    "warehouse": "",
                }
            )

        total_qty = Decimal(str(sum(item.get("qty", 0) for item in po_doc.get("items", []))))
        total_amount = Decimal(str(sum(item.get("amount", 0) for item in po_doc.get("items", []))))
        pr_id = generate_name("PRCP", tenant_id=tenant_id)

        pr_doc = _PurchaseReceiptDraft(
            _id=pr_id,
            tenant_id=tenant_id,
            supplier=po_doc.get("supplier_id", ""),
            supplier_name=po_doc.get("supplier_name", ""),
            posting_date=datetime.now(tz=UTC),
            items=pr_items,
            total_qty=total_qty,
            total_amount=total_amount,
            warehouse="",
            purchase_order_id=doc_id,
        )

        pr_repo = Repository("purchase_receipts", tenant_id=tenant_id)
        pr_repo.insert(pr_doc)

        logger.info(
            "입고전표 초안 생성 완료: %s (구매주문: %s, 아이템 %d건)",
            pr_id,
            doc_id,
            len(pr_items),
        )
        return pr_id
