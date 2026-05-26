"""M3 ehs 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_ehs_app.services.incident_report_pilot_service import (
    IncidentReportPilotService,
    IncidentReportSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = IncidentReportPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "incident_report_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("incident_report_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "INC-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "incident_no": "INC-2026-0001",
            "location": "공장 A동",
            "severity": "minor",
        }
    )
    result = svc.submit("INC-001")
    assert isinstance(result, IncidentReportSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.severity == "minor"
    assert repo.write_outbox.called


def test_차단_EHS_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "INC-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "incident_no": "INC-2026-0002",
            "location": "본사 B동",
            "severity": "major",
        }
    )
    with pytest.raises(ValueError, match=ERR.EHS_001.value) as excinfo:
        svc.submit("INC-002")
    assert excinfo.value.args[0]["code"] == ERR.EHS_001.value
