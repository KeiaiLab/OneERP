"""M3 assets/assets 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_assets_app.services.asset_registration_pilot_service import (
    AssetRegistrationPilotService,
    AssetRegistrationSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = AssetRegistrationPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "asset_registration_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("asset_registration_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "AR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "request_no": "AR-2026-0001",
            "asset_class": "machine",
            "asset_no": "M-001",
        }
    )
    result = svc.submit("AR-001")
    assert isinstance(result, AssetRegistrationSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_AST_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "AR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "request_no": "AR-2026-0002",
            "asset_class": "vehicle",
            "asset_no": "V-001",
        }
    )
    with pytest.raises(ValueError, match=ERR.AST_001.value) as excinfo:
        svc.submit("AR-002")
    assert excinfo.value.args[0]["code"] == ERR.AST_001.value
