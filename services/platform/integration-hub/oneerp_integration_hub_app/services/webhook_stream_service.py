"""WebhookStreamService — M3 platform/integration-hub."""

from __future__ import annotations

from oneerp_core.service_base import EventStreamService


class WebhookStreamService(EventStreamService):
    REPO_KEY = "webhook_event"
    STREAM_NAME = "api.webhook"
