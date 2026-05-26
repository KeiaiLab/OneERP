"""M3 compliance/compliance 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_compliance_app.compliance_mod.services.compliance_review_pilot_service import (
    ComplianceReviewPilotService,
    ComplianceReviewSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ComplianceReviewPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "compliance_review_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("compliance_review_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "CR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "review_no": "CR-2026-0001",
            "regulation": "GDPR",
            "severity": "high",
        }
    )
    result = svc.submit("CR-001")
    assert isinstance(result, ComplianceReviewSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_CMP_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "CR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "review_no": "CR-2026-0002",
            "regulation": "PCI-DSS",
            "severity": "medium",
        }
    )
    with pytest.raises(ValueError, match=ERR.CMP_001.value) as excinfo:
        svc.submit("CR-002")
    assert excinfo.value.args[0]["code"] == ERR.CMP_001.value
