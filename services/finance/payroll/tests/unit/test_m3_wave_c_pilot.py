"""M3 Wave C 파일럿 — payroll PayrollEntryService end-to-end."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_payroll_app.services.payroll_entry_service import (
    PayrollEntryService,
    PayrollEntrySubmissionResult,
)


def _make_svc(doc_raw: dict | None = None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = PayrollEntryService(tenant_id="tenant-1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "payroll_entry"
    repo.write_outbox = MagicMock()
    svc.register_repo("payroll_entry", repo)
    return svc, repo


def test_제출_정상_상태전이() -> None:
    svc, repo = _make_svc(
        {
            "_id": "PE-2026-04",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "entry_no": "PE-2026-04",
            "employee_id": "EMP-001",
            "period": "2026-04",
            "net_pay": {"amount": "3500000", "currency": "KRW"},
        }
    )
    result = svc.submit("PE-2026-04", correlation_id="c-x", idempotency_key="i-y")
    assert isinstance(result, PayrollEntrySubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.net_pay.amount == Decimal(3500000)
    assert repo.write_outbox.called
    subject, payload = repo.write_outbox.call_args[0]
    assert subject == "payroll_entry.submit"
    assert payload["period"] == "2026-04"


def test_이미_SUBMITTED_PAY_001() -> None:
    svc, repo = _make_svc(
        {
            "_id": "PE-2026-03",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "entry_no": "PE-2026-03",
            "employee_id": "EMP-001",
            "period": "2026-03",
            "net_pay": {"amount": "3400000", "currency": "KRW"},
        }
    )
    with pytest.raises(ValueError, match=ERR.PAY_001.value) as excinfo:
        svc.submit("PE-2026-03")
    assert excinfo.value.args[0]["code"] == ERR.PAY_001.value
    assert not repo.write_outbox.called


def test_없는_문서_CMN_NOT_FOUND() -> None:
    svc, _repo = _make_svc(None)
    with pytest.raises(ValueError, match=ERR.CMN_NOT_FOUND.value) as excinfo:
        svc.submit("MISSING")
    assert excinfo.value.args[0]["code"] == ERR.CMN_NOT_FOUND.value
