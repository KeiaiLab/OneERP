"""M3 compliance/clm 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_compliance_app.clm.services.contract_approval_pilot_service import (
    ContractApprovalPilotService,
    ContractApprovalSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ContractApprovalPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "contract_approval_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("contract_approval_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "CA-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "contract_no": "CA-2026-0001",
            "counterparty": "ACME",
            "contract_type": "msa",
        }
    )
    result = svc.submit("CA-001")
    assert isinstance(result, ContractApprovalSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.contract_type == "msa"
    assert repo.write_outbox.called


def test_차단_CLM_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "CA-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "contract_no": "CA-2026-0002",
            "counterparty": "BCorp",
            "contract_type": "nda",
        }
    )
    with pytest.raises(ValueError, match=ERR.CLM_001.value) as excinfo:
        svc.submit("CA-002")
    assert excinfo.value.args[0]["code"] == ERR.CLM_001.value
