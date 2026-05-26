"""G3-4 accounting audit_hooks mutation 테스트.

`audit_hooks.emit` 이 허용 액션·unknown 액션·필수 필드를 올바르게
처리하는지 검증한다. 실제 FerretDB 저장은 `emit_audit_event` 를 mock 하여
호출 인자만 확인한다.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from oneerp_accounting_app import audit_hooks


def test_허용_액션은_그대로_기록된다() -> None:
    """MODULE_ACTIONS 에 포함된 액션은 그대로 전달된다."""
    with patch.object(audit_hooks, "emit_audit_event") as mock_emit:
        audit_hooks.emit(
            actor="user-42",
            action="accounting.post",
            resource="journal_entry:abc",
            tenant_id="tenant-demo",
            details={"amount_total": 1_000_000},
        )

    assert mock_emit.call_count == 1
    event = mock_emit.call_args[0][0]
    assert event.actor == "user-42"
    assert event.action == "accounting.post"
    assert event.resource == "journal_entry:abc"
    assert event.tenant_id == "tenant-demo"
    assert event.details == {"amount_total": 1_000_000}


def test_허용되지_않은_액션은_unknown_으로_기록된다() -> None:
    """MODULE_ACTIONS 외 액션은 `accounting.unknown.<action>` 로 대체 기록."""
    with patch.object(audit_hooks, "emit_audit_event") as mock_emit:
        audit_hooks.emit(
            actor="user-9",
            action="hack.attempt",
            resource="journal_entry:x",
            tenant_id="tenant-demo",
        )

    event = mock_emit.call_args[0][0]
    assert event.action == "accounting.unknown.hack.attempt", (
        "감사 누락 방지를 위해 unknown 액션도 기록되어야 한다"
    )


@pytest.mark.parametrize(
    "action",
    [
        "accounting.create",
        "accounting.update",
        "accounting.delete",
        "accounting.submit",
        "accounting.approve",
        "accounting.post",
        "accounting.reverse",
        "accounting.close",
    ],
)
def test_8개_허용_액션_모두_기록된다(action: str) -> None:
    """ADR-0019 §4 감사 이벤트 8 종이 모두 허용 목록에 있고 기록된다."""
    assert action in audit_hooks.MODULE_ACTIONS
    with patch.object(audit_hooks, "emit_audit_event") as mock_emit:
        audit_hooks.emit(
            actor="actor",
            action=action,
            resource="res",
            tenant_id="t",
        )
    event = mock_emit.call_args[0][0]
    assert event.action == action
    # details 미지정 시 빈 dict 로 정규화
    assert event.details == {}
