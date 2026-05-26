"""M3 collab/projects 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_projects_app.services.project_kickoff_pilot_service import (
    ProjectKickoffPilotService,
    ProjectKickoffSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ProjectKickoffPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "project_kickoff_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("project_kickoff_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "PK-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "project_no": "PK-2026-0001",
            "project_name": "ERP 모듈 확장",
            "sponsor_id": "EMP-100",
        }
    )
    result = svc.submit("PK-001")
    assert isinstance(result, ProjectKickoffSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_PRJ_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "PK-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "project_no": "PK-2026-0002",
            "project_name": "FE 리뉴얼",
            "sponsor_id": "EMP-101",
        }
    )
    with pytest.raises(ValueError, match=ERR.PRJ_001.value) as excinfo:
        svc.submit("PK-002")
    assert excinfo.value.args[0]["code"] == ERR.PRJ_001.value
