"""M3 portal/directory DirectorySyncService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_portal_comms_app.directory.services.directory_sync_service import DirectorySyncService


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = DirectorySyncService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "DSYNC-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("directory_sync_event", repo)
    return svc, repo


def test_직원_추가_동기화_알림() -> None:
    svc, repo = _make_svc()
    result = svc.dispatch(
        recipients=["sso", "ldap", "azure_ad"],
        payload={"event": "employee_added", "employee_id": "EMP-100"},
    )
    assert result["channel"] == "directory_sync"
    assert result["recipient_count"] == 3
    subject, _ = repo.write_outbox.call_args[0]
    assert subject == "notification.directory_sync.dispatched"
