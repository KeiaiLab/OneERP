"""M3 esg 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_finance_extra_app.esg.services.scope_emission_pilot_service import (
    ScopeEmissionPilotService,
    ScopeEmissionSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ScopeEmissionPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "scope_emission_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("scope_emission_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "ESG-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "report_no": "ESG-2026",
            "period": "2026",
            "scope": 1,
        }
    )
    result = svc.submit("ESG-001")
    assert isinstance(result, ScopeEmissionSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.scope == 1
    assert repo.write_outbox.called


def test_차단_ESG_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "ESG-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "report_no": "ESG-2025",
            "period": "2025",
            "scope": 2,
        }
    )
    with pytest.raises(ValueError, match=ERR.ESG_001.value) as excinfo:
        svc.submit("ESG-002")
    assert excinfo.value.args[0]["code"] == ERR.ESG_001.value
