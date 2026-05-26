"""M3 sales/subscriptions 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_commerce_app.subscriptions.services.subscription_plan_pilot_service import (
    SubscriptionPlanPilotService,
    SubscriptionPlanSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = SubscriptionPlanPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "subscription_plan_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("subscription_plan_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "SUB-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "plan_no": "SUB-2026-0001",
            "customer_id": "C-100",
            "plan_tier": "premium",
        }
    )
    result = svc.submit("SUB-001")
    assert isinstance(result, SubscriptionPlanSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_SUB_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "SUB-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "plan_no": "SUB-2026-0002",
            "customer_id": "C-101",
            "plan_tier": "basic",
        }
    )
    with pytest.raises(ValueError, match=ERR.SUB_001.value) as excinfo:
        svc.submit("SUB-002")
    assert excinfo.value.args[0]["code"] == ERR.SUB_001.value
