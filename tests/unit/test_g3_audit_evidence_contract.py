from __future__ import annotations

from scripts.ci.record_g3_audit_evidence import audit_hook_status


def test_audit_hook_status_reads_existing_shared_hook() -> None:
    status = audit_hook_status("selling")

    assert status["audit_hooks_found"] >= 1
    assert status["audit_actions_defined"] >= 5
    assert status["emit_helper_found"] == 1
    assert status["audit_hook_lines"] >= 20
