"""PayrollEntryService — M3 Wave C 파일럿 (payroll 도메인).

M2 selling / M3 Wave B (buying) 파일럿과 동일 구조의 payroll 적용.
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


class PayrollEntryPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    """급여 항목 도메인 모델."""

    entry_no: str = ""
    employee_id: str = ""
    period: str = ""  # YYYY-MM
    net_pay: MonetaryValue = MonetaryValue(amount=Decimal(0), currency="KRW")


class PayrollEntrySubmissionResult(ResponseDTO):
    """급여 항목 제출 결과 응답 DTO."""

    id: str
    entry_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    net_pay: MonetaryValue


class PayrollEntryService(DomainService):
    """payroll 도메인 서비스 — M3 Wave C 파일럿."""

    REPO_ENTRY = "payroll_entry"

    def submit(
        self,
        entry_id: str,
        *,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> PayrollEntrySubmissionResult:
        """급여 항목 제출 — 상태 전이 + 이벤트 발행."""
        repo = self.repo(self.REPO_ENTRY)
        doc_raw = repo.find_by_id(entry_id)

        if doc_raw is None:
            raise ValueError({"code": ERR.CMN_NOT_FOUND.value, "id": entry_id})

        doc = PayrollEntryPilotDoc.model_validate(doc_raw)

        if not doc.can_submit():
            raise ValueError(
                {
                    "code": ERR.PAY_001.value,
                    "current_docstatus": int(doc.docstatus),
                }
            )

        doc.docstatus = DocStatus.SUBMITTED
        doc.approval_status = ApprovalStatus.PENDING
        repo.update(entry_id, doc.model_dump())

        emit_doc_event(
            doc,
            "submit",
            repo=repo,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            extra={"net_pay": str(doc.net_pay.amount), "period": doc.period},
        )

        return PayrollEntrySubmissionResult.from_doc(doc)

    @staticmethod
    def build_from_raw(raw: dict[str, Any]) -> PayrollEntryPilotDoc:
        return PayrollEntryPilotDoc.model_validate(raw)
