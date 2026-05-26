"""파일럿 3 게이트(G1-1/G1-4/G4-2) 단위 테스트 — 누락 시 NOT_IMPLEMENTED."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.gates.g1_docs import gate_G1_1_adr
from scripts.audit.gates.g1_tests import gate_G1_4_unit
from scripts.audit.gates.g4_ops import gate_G4_2_runbook
from scripts.engine.validators import GateStatus


def test_G1_1_adr_missing_is_not_implemented(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADR 파일 없으면 NOT_IMPLEMENTED."""
    monkeypatch.chdir(tmp_path)
    Path("docs/governance/adr").mkdir(parents=True)
    result = gate_G1_1_adr("G1-1", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED


def test_G1_4_unit_missing_is_not_implemented(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """단위 테스트 디렉토리 없으면 NOT_IMPLEMENTED."""
    monkeypatch.chdir(tmp_path)
    result = gate_G1_4_unit("G1-4", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED


def test_G4_2_runbook_missing_is_not_implemented(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """런북 파일 없으면 NOT_IMPLEMENTED."""
    monkeypatch.chdir(tmp_path)
    result = gate_G4_2_runbook("G4-2", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED
