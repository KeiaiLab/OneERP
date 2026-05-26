"""backfill_module_stubs.eligible_gates · place_stub 테스트.

why:
    실 파일이 존재하지 않는 gate 를 stub 하지 않음을 보증한다(진실 경계).
    또한 stub payload 가 실 파일 경로를 인용함을 검증한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.ci.backfill_module_stubs import backfill, eligible_gates, place_stub

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_eligible_gates_for_accounting_includes_G1_2_and_G3_4() -> None:
    """accounting — openapi + audit_hooks 존재 → G1-2 · G3-4 허용."""
    plan = eligible_gates("accounting")
    assert "G1-2" in plan
    assert "G3-4" in plan
    # openapi 경로 인용 확인
    g1_2 = cast("dict[str, Any]", plan["G1-2"])
    assert str(g1_2["source_file"]).endswith("services/finance/accounting/openapi.yaml")


def test_eligible_gates_excludes_G4_3_for_accounting() -> None:
    """G4-3~5 드릴 문서는 accounting/hr 범위 외 → 어떤 경우도 포함되지 않음."""
    for module in ("accounting", "hr"):
        plan = eligible_gates(module)
        assert "G4-3" not in plan
        assert "G4-4" not in plan
        assert "G4-5" not in plan


def test_eligible_gates_G1_3_follows_integration_dir_presence() -> None:
    """G1-3 허용은 tests/integration/<module> 존재 여부에 따라 결정된다.

    세션 1 에서 accounting/hr 통합 테스트 3종이 추가되었으므로, 현재 상태에서는
    디렉토리가 존재하여 G1-3 가 허용 셋에 포함되어야 한다.
    """
    int_dir = REPO_ROOT / "tests" / "integration" / "accounting"
    plan = eligible_gates("accounting")
    if int_dir.exists() and any(int_dir.glob("test_*.py")):
        assert "G1-3" in plan
    else:
        assert "G1-3" not in plan


def test_eligible_gates_G4_1_follows_grafana_presence() -> None:
    """G4-1 허용은 deploy/monitoring/grafana/<module>-overview.json 존재 여부에 따라 결정된다.

    세션 1 에서 accounting/hr Grafana 대시보드 + alerts 가 추가되었으므로, 현재 상태에서는
    G4-1 가 허용 셋에 포함되어야 한다.
    """
    dash = REPO_ROOT / "deploy" / "monitoring" / "grafana" / "accounting-overview.json"
    alerts = REPO_ROOT / "deploy" / "monitoring" / "alerts" / "accounting.yaml"
    plan = eligible_gates("accounting")
    if dash.exists() and alerts.exists():
        assert "G4-1" in plan
        g4_1 = cast("dict[str, Any]", plan["G4-1"])
        verification = cast("dict[str, int]", g4_1["verification"])
        assert verification["alerts_defined"] >= 5
        assert verification["fired_history_checked"] == 1
        assert verification["panels_defined"] >= 6
    else:
        assert "G4-1" not in plan


def test_stub_payload_references_real_file_path(tmp_path: Path) -> None:
    """place_stub 가 생성하는 stub.json 의 evidence.source_file 은 실 파일을 가리킨다."""
    dest, _sha = place_stub(
        gate="G1-2",
        module="accounting",
        tier="T2",
        timestamp_iso="2026-04-22T15:00:00Z",
        file_ts="20260422T150000Z",
        source_file="services/finance/accounting/openapi.yaml",
        source_lines=146,
        evidence_extra={"schemathesis_exit": 0, "contract_tests": 8},
        verification={"schemathesis_exit": 0},
        base_dir=tmp_path,
    )
    payload = json.loads(dest.read_text())
    assert payload["evidence"]["source_file"] == "services/finance/accounting/openapi.yaml"
    assert payload["evidence"]["source_lines"] == 146
    assert "evidence-exists stub" in payload["note"]
    assert "소급" not in payload["note"]  # gateway 소급 stub 과 구분


def test_stub_payload_references_real_file_path_hr() -> None:
    """hr 모듈도 동일하게 실 파일 참조가 보장된다."""
    plan = eligible_gates("hr")
    assert "G3-3" in plan
    assert plan["G3-3"]["source_file"] == "policies/hr/routes.rego"


@pytest.mark.parametrize("module", ["accounting", "hr"])
def test_backfill_creates_stubs_for_all_eligible(tmp_path: Path, module: str) -> None:
    """backfill() 결과가 eligible_gates 와 정확히 일치하는 gate 셋을 stub 한다."""
    summary = backfill(module, base_dir=tmp_path)
    gates_in_records = {r["gate"] for r in summary["records"]}
    assert gates_in_records == set(summary["eligible_gates"])
    # 각 stub 파일 실제로 존재
    for rec in summary["records"]:
        assert (tmp_path / rec["path"]).exists()
