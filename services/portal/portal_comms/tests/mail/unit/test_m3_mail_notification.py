"""M3 portal/mail NotificationService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_portal_comms_app.mail.services.mail_notification_service import MailNotificationService


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = MailNotificationService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "NOTIF-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("mail_notification", repo)
    return svc, repo


def test_dispatch_정상() -> None:
    svc, repo = _make_svc()
    result = svc.dispatch(
        recipients=["user@example.com", "admin@example.com"],
        payload={"subject": "공지", "body": "..."},
    )
    assert result["channel"] == "email"
    assert result["recipient_count"] == 2
    assert result["status"] == "queued"
    assert repo.write_outbox.called
    subject, _ = repo.write_outbox.call_args[0]
    assert subject == "notification.email.dispatched"


def test_dispatch_채널_override() -> None:
    svc, _repo = _make_svc()
    result = svc.dispatch(
        recipients=["x@y.z"],
        payload={"text": "긴급"},
        channel="urgent_email",
    )
    assert result["channel"] == "urgent_email"
