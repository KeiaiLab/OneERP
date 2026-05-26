"""M3 plm 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_plm_app.services.ecr_pilot_service import ECRPilotService, ECRSubmissionResult


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ECRPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "ecr_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("ecr_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "ECR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "ecr_no": "ECR-2026-0001",
            "part_id": "PART-A",
            "change_reason": "원가 절감",
        }
    )
    result = svc.submit("ECR-001")
    assert isinstance(result, ECRSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.part_id == "PART-A"
    assert repo.write_outbox.called


def test_차단_PLM_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "ECR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "ecr_no": "ECR-2026-0002",
            "part_id": "PART-B",
            "change_reason": "안전성 개선",
        }
    )
    with pytest.raises(ValueError, match=ERR.PLM_001.value) as excinfo:
        svc.submit("ECR-002")
    assert excinfo.value.args[0]["code"] == ERR.PLM_001.value
