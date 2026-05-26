from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agents.ground_truth import (
    GroundTruthMismatch,
    verify_edit,
    verify_edits,
)


def test_파일에_인용이_존재하면_True(tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("def foo():\n    return 1\n", encoding="utf-8")
    assert verify_edit(f, "return 1") is True


def test_파일에_인용이_없으면_False(tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("def foo():\n    return 1\n", encoding="utf-8")
    assert verify_edit(f, "return 999") is False


def test_verify_edits_모두_매치되면_빈_미스_리스트(tmp_path: Path) -> None:
    f1 = tmp_path / "a.py"
    f1.write_text("alpha\n", encoding="utf-8")
    f2 = tmp_path / "b.py"
    f2.write_text("beta\n", encoding="utf-8")
    misses = verify_edits([(f1, "alpha"), (f2, "beta")])
    assert misses == []


def test_verify_edits_미스가_있으면_GroundTruthMismatch_옵션() -> None:
    with pytest.raises(GroundTruthMismatch, match="존재하지 않는 파일"):
        verify_edits(
            [(Path("/nonexistent/x.py"), "irrelevant")],
            raise_on_miss=True,
        )
