"""M3 platform/integration-hub EventStreamService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_integration_hub_app.services.webhook_stream_service import WebhookStreamService


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = WebhookStreamService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "EVT-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("webhook_event", repo)
    return svc, repo


def test_웹훅_수집() -> None:
    svc, repo = _make_svc()
    result = svc.ingest(
        event={"type": "payment.completed", "amount": 100000},
        source="stripe",
        correlation_id="evt-corr-1",
    )
    assert result["event_id"] == "EVT-001"
    assert result["stream"] == "api.webhook"
    assert result["source"] == "stripe"
    assert result["status"] == "ingested"
    subject, payload = repo.write_outbox.call_args[0]
    assert subject == "stream.api.webhook.received"
    assert payload["correlation_id"] == "evt-corr-1"
