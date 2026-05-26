"""M3 portal/messenger NotificationService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_portal_core_app.messenger.services.messenger_notification_service import (
    MessengerNotificationService,
)


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = MessengerNotificationService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "MSG-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("messenger_notification", repo)
    return svc, repo


def test_dispatch_정상() -> None:
    svc, repo = _make_svc()
    result = svc.dispatch(
        recipients=["user-1", "user-2", "user-3"],
        payload={"text": "회의 시작"},
    )
    assert result["channel"] == "in_app"
    assert result["recipient_count"] == 3
    assert repo.insert.called
    assert repo.write_outbox.called
