"""WorkReport 서비스 이벤트 핸들러 — 외부 이벤트 수신 처리.

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
    description="결재승인 → 업무일지 상태 업데이트",
)
async def handle_approval_approved(data: dict[str, Any], event_id: str) -> None:
    """결재 승인 시 업무일지 상태를 approved로 변경한다.

    WorkReport 관련 승인만 처리하며, 다른 문서 유형은 무시한다.
    """
    from oneerp_core.repository import Repository

    tenant_id, doc_id = extract_tenant_and_doc(data)
    event_data = data.get("event", {}).get("data", {})
    source_doc_type = event_data.get("source_doc_type", "") if isinstance(event_data, dict) else ""

    # WorkReport 관련 승인만 처리
    if source_doc_type != "WorkReport":
        return

    repo = Repository("work_reports", tenant_id=tenant_id)
    repo.update_by_id(doc_id, {"status": "approved"})
    logger.info("업무일지 승인 처리: doc_id=%s, event_id=%s", doc_id, event_id)


@event_registry.on(
    EventType.APPROVAL_REQUEST_REJECTED,
    description="결재반려 → 업무일지 상태 업데이트",
)
async def handle_approval_rejected(data: dict[str, Any], event_id: str) -> None:
    """결재 반려 시 업무일지 상태를 rejected로 변경한다.

    WorkReport 관련 반려만 처리한다.
    """
    from oneerp_core.repository import Repository

    tenant_id, doc_id = extract_tenant_and_doc(data)
    event_data = data.get("event", {}).get("data", {})
    source_doc_type = event_data.get("source_doc_type", "") if isinstance(event_data, dict) else ""

    if source_doc_type != "WorkReport":
        return

    repo = Repository("work_reports", tenant_id=tenant_id)
    repo.update_by_id(doc_id, {"status": "rejected"})
    logger.info("업무일지 반려 처리: doc_id=%s, event_id=%s", doc_id, event_id)
