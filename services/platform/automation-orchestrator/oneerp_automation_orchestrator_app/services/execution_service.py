"""실행 큐 등록 서비스."""

from __future__ import annotations

from uuid import uuid4

from oneerp_automation_orchestrator_app.models.queue_item import QueueItem


class ExecutionService:
    """자동화 실행을 큐에 등록한다."""

    def enqueue(
        self,
        automation_id: str,
        version: int,
        input_params: dict,
        priority: str,
    ) -> dict:
        run_id = f"ARUN-STUB-{uuid4().hex[:12].upper()}"
        queue_item = QueueItem(
            run_id=run_id,
            automation_id=automation_id,
            version=version,
            status="queued",
            priority=priority,
            input_params=input_params,
        )
        return queue_item.model_dump()
