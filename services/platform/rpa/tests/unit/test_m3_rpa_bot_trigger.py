"""M3 platform/rpa TriggerService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_rpa_app.services.rpa_bot_trigger_service import RPABotTriggerService


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = RPABotTriggerService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "BOT-EXEC-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("rpa_bot_execution", repo)
    return svc, repo


def test_rpa_봇_트리거() -> None:
    svc, repo = _make_svc()
    result = svc.trigger(
        rule_id="BOT-INVOICE-001",
        context={"target_url": "https://erp.example.com", "credentials_ref": "vault:rpa-1"},
    )
    assert result["execution_id"] == "BOT-EXEC-001"
    assert result["trigger_type"] == "rpa_bot"
    subject, _ = repo.write_outbox.call_args[0]
    assert subject == "trigger.rpa_bot.fired"
