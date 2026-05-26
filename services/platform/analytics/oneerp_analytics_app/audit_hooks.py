"""analytics 감사 훅 — G3-4 audit log gate 용 실제 구현.

이 모듈의 변경 작업(CRUD·상태 전이) 은 emit_audit_event 로 audit_events
컬렉션에 기록된다. 각 route 가 감사가 필요한 시점에 emit() 헬퍼를 호출.

ADR-0001 §6.3 G3-4 "모든 변경은 who·what·when·tenant_id 를 남긴다".
"""

from __future__ import annotations

from oneerp_core.audit import AuditEvent, emit_audit_event

__all__ = ["MODULE_ACTIONS", "emit"]

MODULE_ACTIONS: tuple[str, ...] = (
    "analytics.create",
    "analytics.update",
    "analytics.delete",
    "analytics.submit",
    "analytics.approve",
    "analytics.reject",
    "analytics.cancel",
)


def emit(
    *,
    actor: str,
    action: str,
    resource: str,
    tenant_id: str,
    details: dict | None = None,
) -> None:
    """analytics 변경 이벤트를 audit_log 에 기록."""
    if action not in MODULE_ACTIONS:
        # 허용 액션 외 호출 시 경고만 남기고 기록은 수행 (감사 누락 금지).
        action = f"analytics.unknown.{action}"
    emit_audit_event(
        AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            tenant_id=tenant_id,
            details=details or {},
        ),
    )
