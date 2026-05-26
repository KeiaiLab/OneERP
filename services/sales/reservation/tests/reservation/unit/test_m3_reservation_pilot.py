"""M3 sales/reservation 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_reservation_app.reservation.services.reservation_pilot_service import (
    ReservationPilotService,
    ReservationSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ReservationPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "reservation_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("reservation_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "RSV-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "reservation_no": "RSV-2026-0001",
            "resource_id": "ROOM-A",
            "starts_at": "2026-04-15T10:00:00+09:00",
        }
    )
    result = svc.submit("RSV-001")
    assert isinstance(result, ReservationSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_RSV_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "RSV-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "reservation_no": "RSV-2026-0002",
            "resource_id": "ROOM-B",
            "starts_at": "2026-04-13T14:00:00+09:00",
        }
    )
    with pytest.raises(ValueError, match=ERR.RSV_001.value) as excinfo:
        svc.submit("RSV-002")
    assert excinfo.value.args[0]["code"] == ERR.RSV_001.value
