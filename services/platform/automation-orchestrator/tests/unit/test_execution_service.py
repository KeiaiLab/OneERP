"""실행 서비스 테스트."""

from __future__ import annotations

from oneerp_automation_orchestrator_app.services.execution_service import ExecutionService


def test_enqueue_creates_queued_run() -> None:
    service = ExecutionService()

    run = service.enqueue(
        automation_id="AUTO-T001-00001",
        version=1,
        input_params={"period": "2026-03"},
        priority="high",
    )

    assert run["run_id"].startswith("ARUN-STUB-")
    assert run["status"] == "queued"
    assert run["priority"] == "high"
