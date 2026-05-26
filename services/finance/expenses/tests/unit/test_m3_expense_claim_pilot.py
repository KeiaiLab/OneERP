"""M3 Wave B2 — expenses ExpenseClaimService 파일럿 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_expenses_app.services.expense_claim_service import (
    ExpenseClaimService,
    ExpenseClaimSubmissionResult,
)


def _make_svc(doc_raw: dict | None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = ExpenseClaimService(tenant_id="tenant-1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "expense_claim"
    repo.write_outbox = MagicMock()
    svc.register_repo("expense_claim", repo)
    return svc, repo


def test_경비청구_제출() -> None:
    svc, repo = _make_svc(
        {
            "_id": "EXP-001",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "claim_no": "EXP-2026-0001",
            "employee_id": "EMP-001",
            "purpose": "출장 - 부산",
            "total_amount": {"amount": "350000", "currency": "KRW"},
        }
    )
    result = svc.submit("EXP-001", correlation_id="c", idempotency_key="i")
    assert isinstance(result, ExpenseClaimSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.total_amount.amount == Decimal(350000)
    assert repo.write_outbox.called


def test_이미_제출된_경비청구_차단() -> None:
    svc, _ = _make_svc(
        {
            "_id": "EXP-002",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "claim_no": "EXP-2026-0002",
            "employee_id": "EMP-002",
            "purpose": "도서 구매",
            "total_amount": {"amount": "50000", "currency": "KRW"},
        }
    )
    with pytest.raises(ValueError, match=ERR.CMN_VALIDATION.value) as excinfo:
        svc.submit("EXP-002")
    assert excinfo.value.args[0]["code"] == ERR.CMN_VALIDATION.value
