"""G3-4 audit_hooks 최소 mutation 검증 (3건).

`audit_hooks.emit` 의 핵심 불변을 박제한다 — 허용 액션 화이트리스트, unknown
액션의 강제 라벨링, AuditEvent 필드 전달.
"""

from __future__ import annotations

from unittest.mock import patch

from oneerp_hr_app import audit_hooks


def test_화이트리스트에_포함된_액션은_그대로_emit된다() -> None:
    """MODULE_ACTIONS 안 액션은 prefix 재가공 없이 기록."""
    with patch("oneerp_hr_app.audit_hooks.emit_audit_event") as spy:
        audit_hooks.emit(
            actor="u-1",
            action="hr.create",
            resource="Employee/EMP-1",
            tenant_id="t-1",
            details={"k": "v"},
        )
    assert spy.call_count == 1
    event = spy.call_args.args[0]
    assert event.action == "hr.create"
    assert event.actor == "u-1"
    assert event.tenant_id == "t-1"


def test_화이트리스트_외_액션은_unknown_접두사로_라벨링된다() -> None:
    """감사 누락 방지 — 알 수 없는 액션은 hr.unknown.* 으로 강제 기록."""
    with patch("oneerp_hr_app.audit_hooks.emit_audit_event") as spy:
        audit_hooks.emit(
            actor="u-2",
            action="payroll.paid",  # hr 화이트리스트 외
            resource="Payroll/P-1",
            tenant_id="t-1",
        )
    event = spy.call_args.args[0]
    assert event.action == "hr.unknown.payroll.paid"


def test_details_기본값은_빈_dict() -> None:
    """details 미지정 시 AuditEvent 에 빈 dict 가 전달되어 None 차단."""
    with patch("oneerp_hr_app.audit_hooks.emit_audit_event") as spy:
        audit_hooks.emit(
            actor="u-3",
            action="hr.update",
            resource="Employee/EMP-2",
            tenant_id="t-2",
        )
    event = spy.call_args.args[0]
    assert event.details == {}
