"""M3 sales/ecommerce 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_commerce_app.ecommerce.services.ecommerce_order_pilot_service import (
    EcommerceOrderPilotService,
    EcommerceOrderSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = EcommerceOrderPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "ecommerce_order_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("ecommerce_order_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "EO-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "order_no": "EO-2026-0001",
            "customer_id": "C-100",
            "total_amount": 50000,
        }
    )
    result = svc.submit("EO-001")
    assert isinstance(result, EcommerceOrderSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_ECM_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "EO-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "order_no": "EO-2026-0002",
            "customer_id": "C-101",
            "total_amount": 30000,
        }
    )
    with pytest.raises(ValueError, match=ERR.ECM_001.value) as excinfo:
        svc.submit("EO-002")
    assert excinfo.value.args[0]["code"] == ERR.ECM_001.value
