"""M3 portal 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_portal_core_app.portal.services.access_request_pilot_service import (
    AccessRequestPilotService,
    AccessRequestSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = AccessRequestPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "access_request_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("access_request_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "AR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "request_no": "AR-2026-0001",
            "requester_id": "EMP-200",
            "target_resource": "role:finance_admin",
        }
    )
    result = svc.submit("AR-001")
    assert isinstance(result, AccessRequestSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_PRT_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "AR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "request_no": "AR-2026-0002",
            "requester_id": "EMP-201",
            "target_resource": "module:hr",
        }
    )
    with pytest.raises(ValueError, match=ERR.PRT_001.value) as excinfo:
        svc.submit("AR-002")
    assert excinfo.value.args[0]["code"] == ERR.PRT_001.value
