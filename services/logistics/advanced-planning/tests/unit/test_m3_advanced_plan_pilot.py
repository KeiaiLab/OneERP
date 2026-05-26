"""M3 logistics/advanced-planning 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_advanced_planning_app.services.advanced_plan_pilot_service import (
    AdvancedPlanPilotService,
    AdvancedPlanSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = AdvancedPlanPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "advanced_plan_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("advanced_plan_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "AP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "plan_no": "AP-2026-Q3",
            "horizon": "Q3-Q4",
            "plan_type": "production",
        }
    )
    result = svc.submit("AP-001")
    assert isinstance(result, AdvancedPlanSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_APL_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "AP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "plan_no": "AP-2026-Q2",
            "horizon": "Q2",
            "plan_type": "distribution",
        }
    )
    with pytest.raises(ValueError, match=ERR.APL_001.value) as excinfo:
        svc.submit("AP-002")
    assert excinfo.value.args[0]["code"] == ERR.APL_001.value
