"""Accounting 서비스 이벤트 핸들러 패키지."""

from __future__ import annotations

from oneerp_core.events.handlers import register_global_handlers_on
from oneerp_core.events.schemas import EventType

from .handlers import event_registry

# Wave 5-N: core reference 핸들러를 accounting 서비스 registry 에 병합.
# - JOURNAL_ENTRY_SUBMITTED → 분개_승인_원장_감사로그 (core ref, HTTP dispatch)
#   로컬 핸들러가 없으므로 병합한다.
# - PAYROLL_ENTRY_SUBMITTED 는 로컬 handle_payroll_entry_submitted 가 이미
#   분개를 직접 생성하므로 병합하지 않는다 (loopback 방지).
register_global_handlers_on(
    event_registry,
    [EventType.JOURNAL_ENTRY_SUBMITTED],
)

__all__ = ["event_registry"]
