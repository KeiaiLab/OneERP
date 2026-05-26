"""게이트 경로 alias 단위 테스트 — G1-1 ADR · G5-1 매뉴얼 · G5-2 튜토리얼.

why:
    엔진 기본 경로와 실제 레포 구조가 불일치하여 accounting/hr 가 부당하게
    NOT_IMPLEMENTED 로 집계되던 문제를 방지한다. 두 경로 모두 동등 증거로
    수용되어야 한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.gates.g1_docs import gate_G1_1_adr
from scripts.audit.gates.g5_docs import gate_G5_1_manual, gate_G5_2_tutorial
from scripts.engine.validators import GateStatus

# 최소 ADR frontmatter + 본문 (≥ 100 line 보장)
_ADR_BODY = (
    "---\n"
    "status: accepted\n"
    "date: 2026-04-22\n"
    "decision: 모듈 경계 확정\n"
    "consequences: 경계 재조정 시 본 ADR 개정 필요\n"
    "---\n"
    "\n"
    "# ADR — 경계 확정\n"
    "\n" + "본문 필러 라인\n" * 120
)


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_g1_1_accepts_both_governance_and_kb_adr_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G1-1 이 docs/governance/adr 또는 docs/kb/adr 양쪽 모두 인정한다."""
    monkeypatch.chdir(tmp_path)

    # 1) governance/adr 경로 (기존)
    _write(Path("docs/governance/adr/0001-foo-bounds.md"), _ADR_BODY)
    assert gate_G1_1_adr("G1-1", "foo").status == GateStatus.PASS

    # 2) kb/adr 경로 (신규 alias) — 모듈을 바꿔 양측이 독립임을 검증
    _write(Path("docs/kb/adr/0019-bar-bounds.md"), _ADR_BODY)
    assert gate_G1_1_adr("G1-1", "bar").status == GateStatus.PASS

    # 3) 둘 다 없으면 NOT_IMPLEMENTED 유지
    assert gate_G1_1_adr("G1-1", "baz").status == GateStatus.NOT_IMPLEMENTED


def test_g5_1_accepts_both_manual_and_user_manual_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G5-1 이 docs/user-manual 또는 docs/manual 경로 모두 탐지 후보로 수용한다."""
    monkeypatch.chdir(tmp_path)

    # docs/manual 만 존재해도 path alias 가 파일을 찾아야 한다.
    short_manual = "---\nmodule: acc\n---\n# manual\n짧음\n"
    _write(Path("docs/manual/acc.md"), short_manual)
    result = gate_G5_1_manual("G5-1", "acc")
    # 라인 수가 부족하므로 FAIL 이지만, 파일은 발견되어야 한다 (doc missing 이 아님).
    assert "doc missing" not in result.reason
    assert result.status in {GateStatus.FAIL, GateStatus.NOT_IMPLEMENTED}

    # docs/user-manual 에만 파일이 있어도 동일하게 탐지되어야 한다.
    _write(Path("docs/user-manual/um.md"), short_manual)
    result2 = gate_G5_1_manual("G5-1", "um")
    assert "doc missing" not in result2.reason


def test_g5_2_accepts_both_tutorial_and_tutorials_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G5-2 가 docs/tutorials/<m>.md 또는 docs/tutorial/<m>-flow.md 를 모두 인정한다."""
    monkeypatch.chdir(tmp_path)

    short_tut = "---\nmodule: tx\n---\n# tutorial\n짧음\n"
    _write(Path("docs/tutorial/tx-flow.md"), short_tut)
    r1 = gate_G5_2_tutorial("G5-2", "tx")
    assert "doc missing" not in r1.reason

    _write(Path("docs/tutorials/ty.md"), short_tut)
    r2 = gate_G5_2_tutorial("G5-2", "ty")
    assert "doc missing" not in r2.reason

    # 둘 다 없으면 기존 동작 — doc missing NOT_IMPLEMENTED
    r3 = gate_G5_2_tutorial("G5-2", "missing")
    assert r3.status == GateStatus.NOT_IMPLEMENTED
    assert "doc missing" in r3.reason
