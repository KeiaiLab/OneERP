"""M3 manufacturing 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_manufacturing_app.services.work_order_pilot_service import (
    WorkOrderPilotService,
    WorkOrderSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = WorkOrderPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "work_order_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("work_order_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "WO-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "work_order_no": "WO-2026-0001",
            "item_code": "ITEM-A",
            "qty": 100,
        }
    )
    result = svc.submit("WO-001")
    assert isinstance(result, WorkOrderSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert repo.write_outbox.called


def test_차단_MFG_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "WO-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "work_order_no": "WO-2026-0002",
            "item_code": "ITEM-B",
            "qty": 50,
        }
    )
    with pytest.raises(ValueError, match=ERR.MFG_001.value) as excinfo:
        svc.submit("WO-002")
    assert excinfo.value.args[0]["code"] == ERR.MFG_001.value
