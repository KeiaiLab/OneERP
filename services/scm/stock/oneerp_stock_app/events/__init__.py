"""Stock 서비스 이벤트 패키지."""

from __future__ import annotations

from oneerp_core.events.handlers import register_global_handlers_on

from .handlers import event_registry

# Wave 5-N: core reference 핸들러를 글로벌 레지스트리에 자동 등록
# (oneerp_core.events.handlers import 만으로 side-effect 등록됨).
# stock 서비스는 이미 PURCHASE_RECEIPT_SUBMITTED / SALES_ORDER_SUBMITTED 에
# 자체 비즈니스 핸들러를 등록하고 있으므로, core reference 핸들러를 병합하지
# 는 않는다 (중복 호출 방지). 글로벌 레지스트리 접근이 필요한 통합 테스트를
# 위해 import 만 수행한다.
register_global_handlers_on(event_registry, [])

__all__ = ["event_registry"]
