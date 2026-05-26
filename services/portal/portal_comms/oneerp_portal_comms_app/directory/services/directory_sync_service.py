"""DirectorySyncService — M3 portal/directory (디렉토리 동기화 알림)."""

from __future__ import annotations

from oneerp_core.service_base import NotificationService


class DirectorySyncService(NotificationService):
    """디렉토리 변경(직원 추가·이동·퇴사)을 다른 시스템에 알림으로 전파."""

    REPO_KEY = "directory_sync_event"
    DEFAULT_CHANNEL = "directory_sync"
