"""RPABotTriggerService — M3 platform/rpa."""

from __future__ import annotations

from oneerp_core.service_base import TriggerService


class RPABotTriggerService(TriggerService):
    REPO_KEY = "rpa_bot_execution"
    TRIGGER_TYPE = "rpa_bot"
