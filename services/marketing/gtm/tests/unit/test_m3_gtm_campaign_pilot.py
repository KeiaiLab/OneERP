"""M3 marketing/gtm 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_gtm_app.services.gtm_campaign_pilot_service import (
    GTMCampaignPilotService,
    GTMCampaignSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = GTMCampaignPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "gtm_campaign_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("gtm_campaign_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "GTM-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "campaign_no": "GTM-2026-A",
            "product": "신제품 A",
            "region": "KR",
        }
    )
    result = svc.submit("GTM-001")
    assert isinstance(result, GTMCampaignSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_GTM_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "GTM-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "campaign_no": "GTM-2026-B",
            "product": "신제품 B",
            "region": "JP",
        }
    )
    with pytest.raises(ValueError, match=ERR.GTM_001.value) as excinfo:
        svc.submit("GTM-002")
    assert excinfo.value.args[0]["code"] == ERR.GTM_001.value
