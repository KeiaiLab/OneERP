"""SalesInvoiceService — M2 selling 파일럿 서비스.

M1 커널(ApprovalMixin / MonetaryValue / UnitOfWork / DomainService /
emit_doc_event / ErrorCatalog / ResponseDTO) 의 end-to-end 적용 레퍼런스.
M3 Wave A 이후 다른 transactional 도큐먼트(JournalEntry / PurchaseInvoice
/ Expense 등) 를 이 구조로 확산 예정.

원칙 준수:
  P1 ApprovalMixin      — SalesInvoicePilotDoc 이 상속
  P2 Route → Service    — route 는 svc.submit(...) 만 호출
  P3 emit_doc_event     — submit/cancel 시 단일 API 사용
  P4 DTO 격리           — InvoiceSubmissionResult 는 ResponseDTO 기반
  P7 ErrorCatalog       — raise 시 ERR.* enum 만 사용
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


class SalesInvoicePilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    """파일럿 — 판매 송장 도메인 모델.

    M3 에서 기존 SalesInvoice Pydantic 모델을 이 형태(ApprovalMixin +
    SubmitTransitionMixin + MonetaryValue 필드)로 리팩터할 때의 목표 shape.
    """

    invoice_no: str = ""
    customer_id: str = ""
    grand_total: MonetaryValue = MonetaryValue(amount=Decimal(0), currency="KRW")


class InvoiceSubmissionResult(ResponseDTO):
    """송장 제출 결과 응답 DTO."""

    id: str
    invoice_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    grand_total: MonetaryValue


class SalesInvoiceService(DomainService):
    """selling 도메인 서비스 — M2 파일럿."""

    REPO_INVOICE = "sales_invoice"

    def submit(
        self,
        invoice_id: str,
        *,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> InvoiceSubmissionResult:
        """송장 제출 — 상태 전이 + 이벤트 발행 + UoW commit.

        Raises:
            ValueError: ERR.SELL_048 (마감/제출 불가 상태).
        """
        repo = self.repo(self.REPO_INVOICE)
        doc_raw = repo.find_by_id(invoice_id)

        if doc_raw is None:
            raise ValueError({"code": ERR.CMN_NOT_FOUND.value, "id": invoice_id})

        doc = SalesInvoicePilotDoc.model_validate(doc_raw)

        if not doc.can_submit():
            raise ValueError(
                {
                    "code": ERR.SELL_048.value,
                    "current_docstatus": int(doc.docstatus),
                }
            )

        # 상태 전이
        doc.docstatus = DocStatus.SUBMITTED
        doc.approval_status = ApprovalStatus.PENDING
        repo.update(invoice_id, doc.model_dump())

        # 이벤트 단일 API
        emit_doc_event(
            doc,
            "submit",
            repo=repo,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            extra={"grand_total": str(doc.grand_total.amount)},
        )

        return InvoiceSubmissionResult.from_doc(doc)

    @staticmethod
    def build_from_raw(raw: dict[str, Any]) -> SalesInvoicePilotDoc:
        """Repository 반환 dict 를 도메인 모델로 변환 (테스트·디버그용)."""
        return SalesInvoicePilotDoc.model_validate(raw)
