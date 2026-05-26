"""M3 sales/rental 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_reservation_app.rental.services.rental_contract_pilot_service import (
    RentalContractPilotService,
    RentalContractSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = RentalContractPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "rental_contract_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("rental_contract_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "RNT-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "contract_no": "RNT-2026-0001",
            "asset_id": "A-001",
            "customer_id": "C-100",
        }
    )
    result = svc.submit("RNT-001")
    assert isinstance(result, RentalContractSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_RNT_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "RNT-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "contract_no": "RNT-2026-0002",
            "asset_id": "A-002",
            "customer_id": "C-101",
        }
    )
    with pytest.raises(ValueError, match=ERR.RNT_001.value) as excinfo:
        svc.submit("RNT-002")
    assert excinfo.value.args[0]["code"] == ERR.RNT_001.value
