"""Reservation 서비스 이벤트 핸들러 — 결재승인 → 예약 확정.

app_factory._build_event_lifespan에서 핸들러를 호출할 때
시그니처는 (data: dict, event_id: str) 형태이다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(
    EventType.APPROVAL_REQUEST_APPROVED,
    description="결재승인 → 예약 확정",
)
async def handle_approval_approved(data: dict[str, Any], event_id: str) -> None:
    """결재 승인 시 예약 상태를 confirmed로 변경한다.

    Reservation 관련 승인만 처리하며, 다른 문서 유형은 무시한다.
    """
    from oneerp_core.repository import Repository

    tenant_id, doc_id = extract_tenant_and_doc(data)
    event_data = data.get("event", {}).get("data", {})
    source_doc_type = event_data.get("source_doc_type", "") if isinstance(event_data, dict) else ""

    # Reservation 관련 승인만 처리
    if source_doc_type != "Reservation":
        return

    repo = Repository("reservations", tenant_id=tenant_id)
    repo.update_by_id(doc_id, {"status": "confirmed"})
    logger.info("예약 승인 처리: doc_id=%s, event_id=%s", doc_id, event_id)
