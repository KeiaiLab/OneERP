"""M3 collab/calendar 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_calendar_app.services.calendar_event_pilot_service import (
    CalendarEventPilotService,
    CalendarEventSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = CalendarEventPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "calendar_event_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("calendar_event_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "EV-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "event_no": "EV-2026-0001",
            "title": "전사 워크샵",
            "starts_at": "2026-05-01T09:00:00+09:00",
        }
    )
    result = svc.submit("EV-001")
    assert isinstance(result, CalendarEventSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_CAL_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "EV-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "event_no": "EV-2026-0002",
            "title": "외부 컨퍼런스",
            "starts_at": "2026-04-20T13:00:00+09:00",
        }
    )
    with pytest.raises(ValueError, match=ERR.CAL_001.value) as excinfo:
        svc.submit("EV-002")
    assert excinfo.value.args[0]["code"] == ERR.CAL_001.value
