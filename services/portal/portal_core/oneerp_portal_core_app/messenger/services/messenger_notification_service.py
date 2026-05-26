"""MessengerNotificationService — M3 portal/messenger (인앱 메시지)."""

from __future__ import annotations

from oneerp_core.service_base import NotificationService


class MessengerNotificationService(NotificationService):
    REPO_KEY = "messenger_notification"
    DEFAULT_CHANNEL = "in_app"
