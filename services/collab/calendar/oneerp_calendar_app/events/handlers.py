"""Calendar 서비스 이벤트 핸들러 — 외부 이벤트 수신 시 캘린더 이벤트 자동 생성.

HR 휴가 승인 이벤트를 수신하여 해당 직원의 캘린더에 부재 이벤트를 생성한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(
    EventType.LEAVE_APPLICATION_APPROVED,
    description="휴가 승인 → 캘린더 부재 이벤트 생성",
)
async def handle_leave_approved(payload: dict[str, Any], event_id: str) -> None:
    """HR 서비스에서 휴가가 승인되면 캘린더에 부재 이벤트를 자동 생성한다.

    Calendar 서비스 내부에서 CalendarEvent를 생성하므로
    크로스서비스 DB 직접 쓰기가 발생하지 않는다.
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {})

    employee_id = event_data.get("employee_id", "")
    from_date = event_data.get("from_date", "")
    to_date = event_data.get("to_date", "")
    leave_type = event_data.get("leave_type", "휴가")

    if not employee_id or not from_date or not to_date:
        logger.warning(
            "휴가 승인 이벤트 데이터 불완전: event_id=%s, doc_id=%s",
            event_id,
            doc_id,
        )
        return

    # 직원의 기본 캘린더 조회 (없으면 건너뜀)
    cal_repo = Repository("calendars", tenant_id=tenant_id)
    calendars = cal_repo.find_many(
        {"owner_id": employee_id, "status": "active"},
        limit=1,
    )
    if not calendars:
        logger.info("활성 캘린더가 없어 부재 이벤트를 건너뜁니다")
        return

    calendar_id = calendars[0].get("_id", "")
    evt_repo = Repository("calendar_events", tenant_id=tenant_id)
    evt_repo.insert(
        {
            "calendar_id": calendar_id,
            "title": f"{leave_type} (승인됨)",
            "description": f"휴가 신청 #{doc_id} — {leave_type}",
            "event_type": "out_of_office",
            "start_dt": from_date,
            "end_dt": to_date,
            "all_day": True,
            "organizer_id": employee_id,
            "status": "confirmed",
            "ref_doctype": "leave_application",
            "ref_docname": doc_id,
            "tenant_id": tenant_id,
            "created_at": datetime.now(tz=UTC).isoformat(),
            "updated_at": datetime.now(tz=UTC).isoformat(),
        }
    )

    logger.info(
        "휴가 승인 부재 이벤트 생성: 캘린더=%s, event_id=%s",
        calendar_id,
        event_id,
    )
