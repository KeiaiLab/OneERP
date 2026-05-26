"""매입전표 처리 서비스.

입고전표 제출 → 매입전표(PurchaseInvoice) 초안 자동 생성.

NOTE: PurchaseInvoice 모델은 buying 서비스에 정의되어 있으나,
      크로스서비스 의존성을 피하기 위해 BaseDocument 기반으로 직접 생성한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from oneerp_core.document import BaseDocument
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository
from pydantic import Field

logger = logging.getLogger(__name__)

# 기본 결제 기한 (일)
_DEFAULT_PAYMENT_TERM_DAYS = 30


class _PurchaseInvoiceDraft(BaseDocument):
    """매입전표 초안 생성용 경량 모델.

    buying 서비스의 PurchaseInvoice 모델과 동일한 필드 구조를 가진다.
    크로스서비스 의존성을 피하기 위해 별도 정의한다.
    """

    supplier_id: str = ""
    supplier_name: str = ""
    posting_date: datetime | None = None
    due_date: datetime | None = None
    items: list[dict] = Field(default_factory=list)
    taxes: list[dict] = Field(default_factory=list)
    grand_total: float = 0.0
    outstanding_amount: float = 0.0
    etax_invoice_ref: str | None = None
    purchase_receipt_id: str = ""


class InvoiceHandlerService:
    """매입전표 처리 서비스.

    입고전표 제출 → 매입전표(PurchaseInvoice) 초안 자동 생성.
    """

    def handle_purchase_receipt_submitted(self, event_data: dict, tenant_id: str) -> str | None:
        """입고전표 제출 시 매입전표 초안을 생성한다.

        Returns: 생성된 PurchaseInvoice doc_id, 실패 시 None
        """
        doc_id = event_data.get("doc_id")
        if not doc_id:
            logger.warning("이벤트 데이터에 doc_id가 누락되었습니다: %s", event_data)
            return None

        pr_repo = Repository("purchase_receipts", tenant_id=tenant_id)
        pr_doc = pr_repo.find_by_id(doc_id)
        if not pr_doc:
            logger.warning("입고전표 문서를 찾을 수 없습니다: %s", doc_id)
            return None

        # 매입전표 아이템 매핑
        pi_items = []
        for idx, item in enumerate(pr_doc.get("items", []), start=1):
            qty = item.get("qty", 0)
            rate = item.get("rate", 0.0)
            pi_items.append(
                {
                    "idx": idx,
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "qty": qty,
                    "rate": rate,
                    "amount": qty * rate,
                }
            )

        grand_total = sum(item["amount"] for item in pi_items)
        now = datetime.now(tz=UTC)
        due_date = now + timedelta(days=_DEFAULT_PAYMENT_TERM_DAYS)
        pi_id = generate_name("PI", tenant_id=tenant_id)

        pi_doc = _PurchaseInvoiceDraft(
            _id=pi_id,
            tenant_id=tenant_id,
            supplier_id=pr_doc.get("supplier", ""),
            supplier_name=pr_doc.get("supplier_name", ""),
            posting_date=now,
            due_date=due_date,
            items=pi_items,
            taxes=[],
            grand_total=grand_total,
            outstanding_amount=grand_total,
            etax_invoice_ref=None,
            purchase_receipt_id=doc_id,
        )

        pi_repo = Repository("purchase_invoices", tenant_id=tenant_id)
        pi_repo.insert(pi_doc)

        logger.info(
            "매입전표 초안 생성 완료: %s (입고전표: %s, 총액: %.2f)",
            pi_id,
            doc_id,
            grand_total,
        )
        return pi_id
