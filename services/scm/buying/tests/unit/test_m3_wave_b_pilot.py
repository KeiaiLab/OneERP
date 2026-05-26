"""M3 Wave B 파일럿 — buying PurchaseInvoiceService end-to-end.

M2 selling 파일럿과 동일 구조. M1 커널이 도메인을 가리지 않음을 실증.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_buying_app.services.purchase_invoice_service import (
    PurchaseInvoiceService,
    PurchaseInvoiceSubmissionResult,
)
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _mock_repo(doc_raw: dict | None) -> MagicMock:
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "purchase_invoice"
    repo.write_outbox = MagicMock()
    return repo


def _make_svc(doc_raw: dict | None = None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = PurchaseInvoiceService(tenant_id="tenant-1", uow=uow)
    repo = _mock_repo(doc_raw)
    svc.register_repo("purchase_invoice", repo)
    return svc, repo


def test_제출_정상_DocStatus_SUBMITTED_Approval_PENDING() -> None:
    svc, repo = _make_svc(
        {
            "_id": "PINV-001",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "invoice_no": "PI-2026-0001",
            "supplier_id": "SUP-1",
            "grand_total": {"amount": "200000", "currency": "KRW"},
        }
    )

    result = svc.submit("PINV-001", correlation_id="c1", idempotency_key="i1")
    assert isinstance(result, PurchaseInvoiceSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.grand_total.amount == Decimal(200000)
    assert repo.write_outbox.called
    subject, payload = repo.write_outbox.call_args[0]
    assert subject == "purchase_invoice.submit"
    assert payload["correlation_id"] == "c1"


def test_이미_SUBMITTED_BUY_021() -> None:
    svc, repo = _make_svc(
        {
            "_id": "PINV-002",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "invoice_no": "PI-2026-0002",
            "supplier_id": "SUP-2",
            "grand_total": {"amount": "300000", "currency": "KRW"},
        }
    )
    with pytest.raises(ValueError, match=ERR.BUY_021.value) as excinfo:
        svc.submit("PINV-002")
    assert excinfo.value.args[0]["code"] == ERR.BUY_021.value
    assert not repo.write_outbox.called


def test_없는_문서_CMN_NOT_FOUND() -> None:
    svc, _repo = _make_svc(None)
    with pytest.raises(ValueError, match=ERR.CMN_NOT_FOUND.value) as excinfo:
        svc.submit("MISSING")
    assert excinfo.value.args[0]["code"] == ERR.CMN_NOT_FOUND.value
