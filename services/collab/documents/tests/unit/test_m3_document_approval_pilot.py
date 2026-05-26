"""M3 collab/documents 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_documents_app.services.document_approval_pilot_service import (
    DocumentApprovalPilotService,
    DocumentApprovalSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = DocumentApprovalPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "document_approval_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("document_approval_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "DAR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "request_no": "DAR-2026-0001",
            "document_id": "DOC-A",
            "requester_id": "EMP-100",
        }
    )
    result = svc.submit("DAR-001")
    assert isinstance(result, DocumentApprovalSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_DOC_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "DAR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "request_no": "DAR-2026-0002",
            "document_id": "DOC-B",
            "requester_id": "EMP-101",
        }
    )
    with pytest.raises(ValueError, match=ERR.DOC_001.value) as excinfo:
        svc.submit("DAR-002")
    assert excinfo.value.args[0]["code"] == ERR.DOC_001.value
