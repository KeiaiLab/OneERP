"""M3 logistics/tms 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_logistics_app.tms.services.tms_plan_pilot_service import (
    TMSPlanPilotService,
    TMSPlanSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = TMSPlanPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "tms_plan_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("tms_plan_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "TMS-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "plan_no": "TMS-2026-0001",
            "route": "서울→부산",
            "carrier": "한진",
        }
    )
    result = svc.submit("TMS-001")
    assert isinstance(result, TMSPlanSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_TMS_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "TMS-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "plan_no": "TMS-2026-0002",
            "route": "인천→대전",
            "carrier": "CJ",
        }
    )
    with pytest.raises(ValueError, match=ERR.TMS_001.value) as excinfo:
        svc.submit("TMS-002")
    assert excinfo.value.args[0]["code"] == ERR.TMS_001.value
