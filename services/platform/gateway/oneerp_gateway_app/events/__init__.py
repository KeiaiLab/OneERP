"""Gateway 서비스 이벤트 패키지.

Wave 5-N 에서 신설. gateway 는 결재 워크플로 어댑터로서 core reference
``결재승인_후속액션_디스패치`` 를 NATS 구독에 포함시키기 위해 자체 registry
를 갖는다.
"""

from __future__ import annotations

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.handlers import register_global_handlers_on
from oneerp_core.events.schemas import EventType

# gateway 는 현재 자체 이벤트 핸들러가 없으므로 빈 registry 로 시작한다.
event_registry = EventHandlerRegistry()

# core reference: 결재 승인 후속 액션 디스패처 (HTTP 어댑터) 병합.
register_global_handlers_on(
    event_registry,
    [EventType.APPROVAL_REQUEST_APPROVED],
)

__all__ = ["event_registry"]
