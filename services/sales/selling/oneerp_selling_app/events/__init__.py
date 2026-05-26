"""Selling 서비스 이벤트 패키지."""

from __future__ import annotations

from oneerp_core.events.handlers import register_global_handlers_on

from .handlers import event_registry, handle_opportunity_converted

# Wave 5-N: core reference 핸들러 자동 등록 (side-effect 보장).
# selling 은 SALES_ORDER_SUBMITTED 발행자이므로 별도 구독 병합 없음.
register_global_handlers_on(event_registry, [])

__all__ = ["event_registry", "handle_opportunity_converted"]
