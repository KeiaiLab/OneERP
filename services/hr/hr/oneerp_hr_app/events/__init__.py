"""HR 이벤트 체인 패키지 — accounting 패턴 미러.

`event_registry` 는 서비스 단위 `EventHandlerRegistry` 인스턴스이며,
`handlers.register_handlers(event_registry)` 호출 시 7개 도메인 핸들러가 구독된다.
FastAPI lifespan 연동 시 본 registry 를 core app_factory 에 주입한다.
"""

from __future__ import annotations

from oneerp_core.events import EventHandlerRegistry

event_registry: EventHandlerRegistry = EventHandlerRegistry()

__all__ = ["event_registry"]
