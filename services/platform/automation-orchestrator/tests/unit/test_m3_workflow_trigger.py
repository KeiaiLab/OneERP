"""M3 platform/automation-orchestrator TriggerService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_automation_orchestrator_app.services.workflow_trigger_service import (
    WorkflowTriggerService,
)
from oneerp_core.uow import UnitOfWork


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = WorkflowTriggerService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "EXEC-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("workflow_execution", repo)
    return svc, repo


def test_워크플로_트리거() -> None:
    svc, repo = _make_svc()
    result = svc.trigger(
        rule_id="WF-RULE-001",
        context={"input": {"order_id": "SO-1"}},
        correlation_id="corr-x",
    )
    assert result["execution_id"] == "EXEC-001"
    assert result["trigger_type"] == "workflow"
    assert result["status"] == "started"
    subject, payload = repo.write_outbox.call_args[0]
    assert subject == "trigger.workflow.fired"
    assert payload["correlation_id"] == "corr-x"
