"""M3 Wave A2 — accounting JournalEntryService 파일럿 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_accounting_app.services.journal_entry_pilot_service import (
    JournalEntryService,
    JournalEntrySubmissionResult,
)
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw: dict | None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = JournalEntryService(tenant_id="tenant-1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "journal_entry"
    repo.write_outbox = MagicMock()
    svc.register_repo("journal_entry", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "JE-001",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "entry_no": "JE-2026-0001",
            "posting_date": "2026-04-12",
            "total_debit": {"amount": "150000", "currency": "KRW"},
        }
    )
    result = svc.submit("JE-001", correlation_id="c", idempotency_key="i")
    assert isinstance(result, JournalEntrySubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.total_debit.amount == Decimal(150000)
    assert repo.write_outbox.called
    subject, _ = repo.write_outbox.call_args[0]
    assert subject == "journal_entry.submit"


def test_이미_SUBMITTED_ACCT_002() -> None:
    svc, _repo = _make_svc(
        {
            "_id": "JE-002",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "entry_no": "JE-2026-0002",
            "posting_date": "2026-04-12",
            "total_debit": {"amount": "100000", "currency": "KRW"},
        }
    )
    with pytest.raises(ValueError, match=ERR.ACCT_002.value) as excinfo:
        svc.submit("JE-002")
    assert excinfo.value.args[0]["code"] == ERR.ACCT_002.value


def test_없는_문서_NOT_FOUND() -> None:
    svc, _ = _make_svc(None)
    with pytest.raises(ValueError, match=ERR.CMN_NOT_FOUND.value) as excinfo:
        svc.submit("MISSING")
    assert excinfo.value.args[0]["code"] == ERR.CMN_NOT_FOUND.value
