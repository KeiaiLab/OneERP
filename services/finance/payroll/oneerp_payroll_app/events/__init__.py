"""Payroll 서비스 이벤트 패키지."""

from __future__ import annotations

from oneerp_core.events.handlers import register_global_handlers_on

from .handlers import event_registry, handle_employee_updated

# Wave 5-N: core reference 핸들러 자동 등록 (side-effect 보장).
# payroll 은 PAYROLL_ENTRY_SUBMITTED 발행자이므로 병합 대상 없음.
register_global_handlers_on(event_registry, [])

__all__ = ["event_registry", "handle_employee_updated"]
