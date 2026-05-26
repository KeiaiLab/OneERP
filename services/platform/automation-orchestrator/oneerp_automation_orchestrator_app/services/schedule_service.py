"""스케줄 생성 서비스."""

from __future__ import annotations

from uuid import uuid4


class ScheduleService:
    """자동화 스케줄을 생성한다."""

    def create_schedule(
        self,
        automation_id: str,
        cron: str,
        timezone: str,
    ) -> dict[str, object]:
        schedule_id = f"ASCH-STUB-{uuid4().hex[:12].upper()}"
        return {
            "schedule_id": schedule_id,
            "automation_id": automation_id,
            "cron": cron,
            "timezone": timezone,
        }
