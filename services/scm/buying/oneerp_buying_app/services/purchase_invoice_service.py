"""PurchaseInvoiceService — M3 Wave B 파일럿 (buying 도메인).

M2 selling 파일럿(sales_invoice_service.py) 패턴의 buying 도메인 적용.
M1 커널 9 모듈을 매입 송장에 동일하게 적용해 P1~P7 준수가 도메인을
가리지 않음을 실증.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from oneerp_core.document import (
    ApprovalMixin,
    ApprovalStatus,
    BaseDocument,
    DocStatus,
    MonetaryValue,
    SubmitTransitionMixin,
)
from oneerp_core.dto import ResponseDTO
from oneerp_core.error_catalog import ERR
from oneerp_core.events.bus import emit_doc_event
from oneerp_core.service_base import DomainService


class PurchaseInvoicePilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    """매입 송장 도메인 모델 — M3 Wave B 목표 shape."""

    invoice_no: str = ""
    supplier_id: str = ""
    grand_total: MonetaryValue = MonetaryValue(amount=Decimal(0), currency="KRW")


class PurchaseInvoiceSubmissionResult(ResponseDTO):
    """매입 송장 제출 결과 응답 DTO."""

    id: str
    invoice_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    grand_total: MonetaryValue


class PurchaseInvoiceService(DomainService):
    """buying 도메인 서비스 — M3 Wave B 파일럿."""

    REPO_INVOICE = "purchase_invoice"

    def submit(
        self,
        invoice_id: str,
        *,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> PurchaseInvoiceSubmissionResult:
        """매입 송장 제출 — 상태 전이 + 이벤트 발행."""
        repo = self.repo(self.REPO_INVOICE)
        doc_raw = repo.find_by_id(invoice_id)

        if doc_raw is None:
            raise ValueError({"code": ERR.CMN_NOT_FOUND.value, "id": invoice_id})

        doc = PurchaseInvoicePilotDoc.model_validate(doc_raw)

        if not doc.can_submit():
            raise ValueError(
                {
                    "code": ERR.BUY_021.value,
                    "current_docstatus": int(doc.docstatus),
                }
            )

        doc.docstatus = DocStatus.SUBMITTED
        doc.approval_status = ApprovalStatus.PENDING
        repo.update(invoice_id, doc.model_dump())

        emit_doc_event(
            doc,
            "submit",
            repo=repo,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            extra={"grand_total": str(doc.grand_total.amount)},
        )

        return PurchaseInvoiceSubmissionResult.from_doc(doc)

    @staticmethod
    def build_from_raw(raw: dict[str, Any]) -> PurchaseInvoicePilotDoc:
        return PurchaseInvoicePilotDoc.model_validate(raw)
