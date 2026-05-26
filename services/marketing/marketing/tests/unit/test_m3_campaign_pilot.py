"""M3 marketing 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_marketing_app.services.campaign_pilot_service import (
    CampaignPilotService,
    CampaignSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = CampaignPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "campaign_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("campaign_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "CMP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "campaign_no": "CMP-2026-Q2",
            "name": "Spring Promo",
            "channel": "email",
        }
    )
    result = svc.submit("CMP-001")
    assert isinstance(result, CampaignSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.channel == "email"
    assert repo.write_outbox.called


def test_차단_MKT_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "CMP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "campaign_no": "CMP-2026-Q1",
            "name": "Winter Sale",
            "channel": "sms",
        }
    )
    with pytest.raises(ValueError, match=ERR.MKT_001.value) as excinfo:
        svc.submit("CMP-002")
    assert excinfo.value.args[0]["code"] == ERR.MKT_001.value
