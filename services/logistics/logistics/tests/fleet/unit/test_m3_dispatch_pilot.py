"""M3 fleet 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_logistics_app.fleet.services.dispatch_pilot_service import (
    VehicleDispatchPilotService,
    VehicleDispatchSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = VehicleDispatchPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "vehicle_dispatch_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("vehicle_dispatch_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "DSP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "dispatch_no": "DSP-2026-0001",
            "vehicle_id": "VEH-1",
            "driver_id": "DRV-1",
            "departure_at": "2026-04-13T08:00:00+09:00",
        }
    )
    result = svc.submit("DSP-001")
    assert isinstance(result, VehicleDispatchSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.vehicle_id == "VEH-1"
    assert repo.write_outbox.called


def test_차단_FLT_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "DSP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "dispatch_no": "DSP-2026-0002",
            "vehicle_id": "VEH-2",
            "driver_id": "DRV-2",
            "departure_at": "2026-04-12T09:00:00+09:00",
        }
    )
    with pytest.raises(ValueError, match=ERR.FLT_001.value) as excinfo:
        svc.submit("DSP-002")
    assert excinfo.value.args[0]["code"] == ERR.FLT_001.value
