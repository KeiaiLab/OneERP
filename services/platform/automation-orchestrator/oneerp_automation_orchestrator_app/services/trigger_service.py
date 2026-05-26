"""트리거 생성 서비스."""

from __future__ import annotations

from uuid import uuid4


class TriggerService:
    """자동화 트리거를 생성한다."""

    def create_trigger(
        self,
        automation_id: str,
        trigger_type: str,
        event_name: str | None = None,
        debounce_seconds: int | None = None,
    ) -> dict[str, object]:
        trigger_id = f"ATRG-STUB-{uuid4().hex[:12].upper()}"
        return {
            "trigger_id": trigger_id,
            "automation_id": automation_id,
            "type": trigger_type,
            "event_name": event_name,
            "debounce_seconds": debounce_seconds,
        }
