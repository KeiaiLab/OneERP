"""M3 maintenance 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_qm_app.maintenance.services.maintenance_wo_pilot_service import (
    MaintenanceWOPilotService,
    MaintenanceWOSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = MaintenanceWOPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "maintenance_wo_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("maintenance_wo_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "MWO-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "mwo_no": "MWO-2026-0001",
            "asset_id": "ASSET-1",
            "maintenance_type": "preventive",
        }
    )
    result = svc.submit("MWO-001")
    assert isinstance(result, MaintenanceWOSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.maintenance_type == "preventive"
    assert repo.write_outbox.called


def test_차단_MNT_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "MWO-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "mwo_no": "MWO-2026-0002",
            "asset_id": "ASSET-2",
            "maintenance_type": "corrective",
        }
    )
    with pytest.raises(ValueError, match=ERR.MNT_001.value) as excinfo:
        svc.submit("MWO-002")
    assert excinfo.value.args[0]["code"] == ERR.MNT_001.value
