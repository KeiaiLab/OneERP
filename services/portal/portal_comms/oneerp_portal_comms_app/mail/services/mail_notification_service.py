"""MailNotificationService — M3 portal/mail (이메일 알림)."""

from __future__ import annotations

from oneerp_core.service_base import NotificationService


class MailNotificationService(NotificationService):
    REPO_KEY = "mail_notification"
    DEFAULT_CHANNEL = "email"
