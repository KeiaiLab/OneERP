"""M3 sales/pos 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_pos_app.services.pos_receipt_pilot_service import (
    PosReceiptPilotService,
    PosReceiptSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = PosReceiptPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "pos_receipt_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("pos_receipt_pilot", repo)
    return svc, repo


def test_pos_영수증_제출() -> None:
    svc, repo = _make_svc(
        {
            "_id": "POS-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "receipt_no": "POS-2026-0001",
            "pos_id": "POS-A1",
            "payment_method": "card",
        }
    )
    result = svc.submit("POS-001")
    assert isinstance(result, PosReceiptSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.payment_method == "card"
    assert repo.write_outbox.called


def test_차단_재제출() -> None:
    svc, _ = _make_svc(
        {
            "_id": "POS-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "receipt_no": "POS-2026-0002",
            "pos_id": "POS-A2",
            "payment_method": "cash",
        }
    )
    with pytest.raises(ValueError, match=ERR.CMN_VALIDATION.value) as excinfo:
        svc.submit("POS-002")
    assert excinfo.value.args[0]["code"] == ERR.CMN_VALIDATION.value
