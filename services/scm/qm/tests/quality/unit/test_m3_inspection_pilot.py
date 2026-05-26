"""M3 quality 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_qm_app.quality.services.inspection_pilot_service import (
    InspectionPilotService,
    InspectionSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = InspectionPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "inspection_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("inspection_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "QI-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "inspection_no": "QI-2026-0001",
            "item_code": "ITEM-A",
            "result": "pass",
        }
    )
    result = svc.submit("QI-001")
    assert isinstance(result, InspectionSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.result == "pass"
    assert repo.write_outbox.called


def test_차단_QC_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "QI-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "inspection_no": "QI-2026-0002",
            "item_code": "ITEM-B",
            "result": "fail",
        }
    )
    with pytest.raises(ValueError, match=ERR.QC_001.value) as excinfo:
        svc.submit("QI-002")
    assert excinfo.value.args[0]["code"] == ERR.QC_001.value
