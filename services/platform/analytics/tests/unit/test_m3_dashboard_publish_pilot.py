"""M3 platform/analytics 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_analytics_app.services.dashboard_publish_pilot_service import (
    DashboardPublishPilotService,
    DashboardPublishSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = DashboardPublishPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "dashboard_publish_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("dashboard_publish_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "DP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "publish_no": "DP-2026-0001",
            "dashboard_id": "DASH-FIN",
            "audience": "executives",
        }
    )
    result = svc.submit("DP-001")
    assert isinstance(result, DashboardPublishSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_ANL_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "DP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "publish_no": "DP-2026-0002",
            "dashboard_id": "DASH-OPS",
            "audience": "ops",
        }
    )
    with pytest.raises(ValueError, match=ERR.ANL_001.value) as excinfo:
        svc.submit("DP-002")
    assert excinfo.value.args[0]["code"] == ERR.ANL_001.value
