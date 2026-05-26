"""T2 artifact 수집기 단위 테스트 (TDD).

Spec II 회귀(run-*.json 미수집으로 4셀 PARTIAL)를 차단하기 위한
`scripts.ci.collect_t2_artifacts` 모듈의 공용 API 계약을 잠근다.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from scripts.ci.collect_t2_artifacts import (
    build_expected_globs,
    normalize_artifact_name,
    place_artifact,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_normalize_artifact_name_extracts_gate_module() -> None:
    # why: GitHub Actions artifact 이름 규칙 `t2-<GATE>-<MODULE>-<suffix>` 파싱 보장
    assert normalize_artifact_name("t2-G1-2-accounting-run") == ("G1-2", "accounting")
    assert normalize_artifact_name("t2-G3-1-gateway-ci") == ("G3-1", "gateway")


def test_normalize_artifact_name_rejects_bad_names() -> None:
    # why: 잘못된 이름은 조용히 흘리지 않고 ValueError 로 즉시 실패시켜 CI 회귀를 차단
    with pytest.raises(ValueError, match="bad artifact name"):
        normalize_artifact_name("bad-name")


def test_place_artifact_writes_expected_path(tmp_path: Path) -> None:
    # why: artifacts/T2/<GATE>/<MODULE>/run-<ts>.json 경로 규약 고정
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"ok": True}))
    dest = place_artifact(src, gate="G1-2", module="accounting", root=tmp_path / "out")
    assert dest.exists()
    assert dest.parent == tmp_path / "out" / "T2" / "G1-2" / "accounting"
    assert dest.name.startswith("run-")
    assert dest.suffix == ".json"


def test_build_expected_globs_matches_gate_module_matrix() -> None:
    # why: 게이트/모듈 직교 매트릭스 전수 생성이 수집기/검증기 양측에서 동일해야 함
    globs = build_expected_globs(gates=["G1-2", "G1-3"], modules=["accounting", "hr"])
    assert "artifacts/T2/G1-2/accounting/run-*.json" in globs
    assert "artifacts/T2/G1-3/hr/run-*.json" in globs
    assert len(globs) == 4
