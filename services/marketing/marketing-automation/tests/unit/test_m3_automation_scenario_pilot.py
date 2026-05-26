"""M3 marketing/marketing-automation 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_marketing_automation_app.services.automation_scenario_pilot_service import (
    AutomationScenarioPilotService,
    AutomationScenarioSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = AutomationScenarioPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "automation_scenario_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("automation_scenario_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "AS-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "scenario_no": "AS-2026-0001",
            "name": "신규고객 환영",
            "trigger_event": "user_signup",
        }
    )
    result = svc.submit("AS-001")
    assert isinstance(result, AutomationScenarioSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_MAU_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "AS-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "scenario_no": "AS-2026-0002",
            "name": "리텐션 캠페인",
            "trigger_event": "inactivity_30d",
        }
    )
    with pytest.raises(ValueError, match=ERR.MAU_001.value) as excinfo:
        svc.submit("AS-002")
    assert excinfo.value.args[0]["code"] == ERR.MAU_001.value
