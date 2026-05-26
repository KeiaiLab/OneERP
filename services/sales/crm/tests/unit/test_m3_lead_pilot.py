"""M3 crm 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_crm_app.services.lead_pilot_service import LeadPilotService, LeadSubmissionResult


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = LeadPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "lead_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("lead_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "LD-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "lead_no": "LD-2026-0001",
            "company_name": "ACME",
            "stage": "qualified",
        }
    )
    result = svc.submit("LD-001")
    assert isinstance(result, LeadSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.stage == "qualified"
    assert repo.write_outbox.called


def test_차단_CRM_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "LD-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "lead_no": "LD-2026-0002",
            "company_name": "BCorp",
            "stage": "proposal",
        }
    )
    with pytest.raises(ValueError, match=ERR.CRM_001.value) as excinfo:
        svc.submit("LD-002")
    assert excinfo.value.args[0]["code"] == ERR.CRM_001.value
