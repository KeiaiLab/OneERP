"""G1-3 API 통합 계약 — workreport."""

from __future__ import annotations

from scripts.audit.gates.g1_tests import module_openapi_path

MODULE = "workreport"


def test_openapi_contract_exists_and_has_paths() -> None:
    path = module_openapi_path(MODULE)
    text = path.read_text(encoding="utf-8")

    assert "openapi:" in text
    assert "paths:" in text
    assert "/" in text
