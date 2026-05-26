"""HR event_registry 단위 테스트 — accounting 패턴 미러.

register_handlers 호출 후 employee 이벤트 3종이 구독 등록되어 있는지 검증한다.
"""

from __future__ import annotations

from oneerp_core.events import EventHandlerRegistry
from oneerp_hr_app.events import event_registry
from oneerp_hr_app.events.handlers import register_handlers


def test_event_registry_has_employee_handlers_after_register() -> None:
    """register_handlers 호출 후 employee.hired/terminated/transferred 구독 존재."""
    # 격리: 모듈 import 시 이미 main.py 경로로 등록됐을 수 있으므로 초기화 후 재등록
    registry = EventHandlerRegistry()
    register_handlers(registry)
    names = {sub.event_type.value for sub in registry.subscriptions}
    assert "employee.hired" in names
    assert "employee.terminated" in names
    assert "employee.transferred" in names


def test_module_event_registry_is_registry_instance() -> None:
    """hr 이벤트 패키지가 제공하는 event_registry 는 EventHandlerRegistry 인스턴스."""
    assert isinstance(event_registry, EventHandlerRegistry)
