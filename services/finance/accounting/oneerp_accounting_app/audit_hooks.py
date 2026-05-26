"""accounting 감사 훅 — G3-4 audit log gate 용 실구현.

이 모듈의 변경 작업(CRUD·상태 전이) 은 `emit_audit_event` 로 `audit_events`
컬렉션에 기록된다. 각 route 가 감사가 필요한 시점에 `emit()` 헬퍼를 호출.

ADR-0001 §6.3 G3-4 "모든 변경은 who·what·when·tenant_id 를 남긴다".
ADR-0019 §4 accounting 변경 이벤트 8 종 — MODULE_ACTIONS 에 열거.
"""

from __future__ import annotations

from oneerp_core.audit import AuditEvent, emit_audit_event

__all__ = ["MODULE_ACTIONS", "emit"]

#: 허용되는 accounting 감사 액션. ADR-0019 §4 감사 로그 절 참조.
MODULE_ACTIONS: tuple[str, ...] = (
    "accounting.create",
    "accounting.update",
    "accounting.delete",
    "accounting.submit",
    "accounting.approve",
    "accounting.post",
    "accounting.reverse",
    "accounting.close",
)


def emit(
    *,
    actor: str,
    action: str,
    resource: str,
    tenant_id: str,
    details: dict | None = None,
) -> None:
    """accounting 변경 이벤트를 audit_log 에 기록.

    허용 액션(`MODULE_ACTIONS`) 외 호출은 `accounting.unknown.<action>` 으로
    대체 기록하여 감사 누락을 방지한다.
    """
    if action not in MODULE_ACTIONS:
        action = f"accounting.unknown.{action}"
    emit_audit_event(
        AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            tenant_id=tenant_id,
            details=details or {},
        ),
    )
