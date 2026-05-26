"""M2 파일럿 테스트 — SalesInvoiceService end-to-end.

M1 커널(ApprovalMixin/MonetaryValue/UoW/DomainService/emit_doc_event/
ErrorCatalog/ResponseDTO) 가 실제 선언한 원칙대로 동작하는지 검증.
M3 확산 시 이 테스트가 각 도메인 서비스의 템플릿이 된다.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus, MonetaryValue
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_selling_app.services.sales_invoice_service import (
    InvoiceSubmissionResult,
    SalesInvoicePilotDoc,
    SalesInvoiceService,
)


def _mock_repo_with_doc(doc_raw: dict) -> MagicMock:
    """도큐먼트 하나를 반환하는 Repository mock + write_outbox 캡처."""
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "sales_invoice"
    repo.write_outbox = MagicMock()
    return repo


class Test제출_정상플로우:
    def test_제출시_docstatus_SUBMITTED_approval_PENDING(self) -> None:
        # given: DRAFT 송장
        uow = UnitOfWork(tenant_id="tenant-1")
        svc = SalesInvoiceService(tenant_id="tenant-1", uow=uow)
        repo = _mock_repo_with_doc(
            {
                "_id": "INV-001",
                "tenant_id": "tenant-1",
                "docstatus": DocStatus.DRAFT,
                "invoice_no": "SI-2026-0001",
                "customer_id": "CUST-1",
                "grand_total": {"amount": "100000", "currency": "KRW"},
                "approval_status": ApprovalStatus.NOT_REQUIRED,
            }
        )
        svc.register_repo("sales_invoice", repo)

        result = svc.submit(
            "INV-001",
            correlation_id="corr-abc",
            idempotency_key="idem-xyz",
        )

        # then: Response DTO 에 전이 상태 반영
        assert isinstance(result, InvoiceSubmissionResult)
        assert result.docstatus == DocStatus.SUBMITTED
        assert result.approval_status == ApprovalStatus.PENDING
        assert result.grand_total.amount == Decimal(100000)
        assert result.grand_total.currency == "KRW"

        # Repository.update 호출
        assert repo.update.called

        # emit_doc_event 를 통해 write_outbox 호출됨
        assert repo.write_outbox.called
        subject, payload = repo.write_outbox.call_args[0]
        assert subject == "sales_invoice.submit"
        assert payload["action"] == "submit"
        assert payload["correlation_id"] == "corr-abc"
        assert payload["idempotency_key"] == "idem-xyz"
        # extra 는 emit_doc_event 에서 flat merge 되므로 top-level 에 나타남
        assert payload["grand_total"] == "100000"


class Test제출_차단_규칙:
    def test_이미_SUBMITTED_문서는_SELL_048(self) -> None:
        uow = UnitOfWork(tenant_id="tenant-1")
        svc = SalesInvoiceService(tenant_id="tenant-1", uow=uow)
        repo = _mock_repo_with_doc(
            {
                "_id": "INV-002",
                "tenant_id": "tenant-1",
                "docstatus": DocStatus.SUBMITTED,
                "invoice_no": "SI-2026-0002",
                "customer_id": "CUST-2",
                "grand_total": {"amount": "50000", "currency": "KRW"},
            }
        )
        svc.register_repo("sales_invoice", repo)

        with pytest.raises(ValueError, match="ERR-SELL-048") as excinfo:
            svc.submit("INV-002")

        err = excinfo.value.args[0]
        assert err["code"] == ERR.SELL_048.value
        assert err["current_docstatus"] == int(DocStatus.SUBMITTED)

        # 차단된 경우 Repository.update / emit 호출되지 않아야 함
        assert not repo.update.called
        assert not repo.write_outbox.called

    def test_존재하지_않는_문서는_CMN_NOT_FOUND(self) -> None:
        uow = UnitOfWork(tenant_id="tenant-1")
        svc = SalesInvoiceService(tenant_id="tenant-1", uow=uow)
        repo = MagicMock()
        repo.find_by_id.return_value = None
        svc.register_repo("sales_invoice", repo)

        with pytest.raises(ValueError, match="ERR-CMN-NOT-FOUND") as excinfo:
            svc.submit("MISSING")
        assert excinfo.value.args[0]["code"] == ERR.CMN_NOT_FOUND.value


class Test도메인모델_공통_mixin_동작:
    def test_상태전이_is_draft_이후_is_submitted(self) -> None:
        doc = SalesInvoicePilotDoc(
            tenant_id="tenant-1",
            docstatus=DocStatus.DRAFT,
            invoice_no="X",
            customer_id="C",
        )
        assert doc.is_draft()
        assert not doc.is_submitted()
        assert doc.can_submit()
        assert not doc.can_cancel()

        doc.docstatus = DocStatus.SUBMITTED
        assert not doc.is_draft()
        assert doc.is_submitted()
        assert not doc.can_submit()
        assert doc.can_cancel()

    def test_MonetaryValue_덧셈_통화체크(self) -> None:
        krw_100 = MonetaryValue(amount=Decimal(100), currency="KRW")
        krw_50 = MonetaryValue(amount=Decimal(50), currency="KRW")
        assert (krw_100 + krw_50).amount == Decimal(150)

        usd_10 = MonetaryValue(amount=Decimal(10), currency="USD")
        with pytest.raises(ValueError, match="통화 불일치"):
            _ = krw_100 + usd_10
