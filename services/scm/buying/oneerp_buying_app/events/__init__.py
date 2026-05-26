"""Buying 서비스 이벤트 패키지."""

from __future__ import annotations

from oneerp_core.events.handlers import register_global_handlers_on

from .handlers import event_registry

# Wave 5-N: core reference 핸들러 자동 등록 (side-effect 보장).
# buying 은 이벤트 발행자이므로 core reference 핸들러를 구독할 필요는 없다.
register_global_handlers_on(event_registry, [])

__all__ = ["event_registry"]
