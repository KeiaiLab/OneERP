"""M3 workreport 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_learning_app.workreport.services.weekly_report_pilot_service import (
    WeeklyReportPilotService,
    WeeklyReportSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = WeeklyReportPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "weekly_report_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("weekly_report_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "WR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "report_no": "WR-2026-W15",
            "employee_id": "EMP-100",
            "week_of": "2026-W15",
        }
    )
    result = svc.submit("WR-001")
    assert isinstance(result, WeeklyReportSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.week_of == "2026-W15"
    assert repo.write_outbox.called


def test_차단_WRP_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "WR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "report_no": "WR-2026-W14",
            "employee_id": "EMP-100",
            "week_of": "2026-W14",
        }
    )
    with pytest.raises(ValueError, match=ERR.WRP_001.value) as excinfo:
        svc.submit("WR-002")
    assert excinfo.value.args[0]["code"] == ERR.WRP_001.value
