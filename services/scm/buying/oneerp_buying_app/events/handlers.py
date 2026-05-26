"""Buying 서비스 이벤트 핸들러 — 구매주문 제출 이벤트 처리.

app_factory._build_event_lifespan에서 핸들러를 호출할 때
시그니처는 (data: dict, event_id: str) 형태이다.
data는 EventEnvelope JSON 전체이며, tenant_id는 data["event"]["tenant_id"]에서 추출한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(EventType.PURCHASE_ORDER_SUBMITTED, description="구매주문 제출 → 입고 준비 알림")
async def handle_purchase_order_submitted(data: dict[str, Any], event_id: str) -> None:
    """구매주문 제출 시 입고 준비 로그를 기록한다.

    현재는 로깅만 수행하며, 향후 알림 서비스와 연동할 예정이다.
    """
    _tenant_id, doc_id = extract_tenant_and_doc(data)
    logger.info("구매주문 제출 감지, 입고 준비 필요: doc_id=%s, event_id=%s", doc_id, event_id)
