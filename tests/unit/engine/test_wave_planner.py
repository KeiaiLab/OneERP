"""wave_planner 단위 테스트 — 영역 순위·max_cells·모듈 필터."""

from __future__ import annotations

from scripts.engine.wave_planner import plan_wave


def test_plan_wave_picks_failed_cells_within_module_filter() -> None:
    """지정 모듈의 FAIL/NOT_IMPLEMENTED 만 선택."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-1", "status": "not_implemented"},
                    {"id": "G1-4", "status": "not_implemented"},
                    {"id": "G4-2", "status": "not_implemented"},
                    {"id": "G1-2", "status": "pass"},
                ],
            }
        ]
    }
    plan = plan_wave(status, max_cells=10, modules=["gateway"])
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ids == {("gateway", "G1-1"), ("gateway", "G1-4"), ("gateway", "G4-2")}


def test_plan_wave_respects_max_cells() -> None:
    """max_cells 로 타겟 수 제한."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [{"id": f"G1-{i}", "status": "not_implemented"} for i in range(1, 6)],
            }
        ]
    }
    plan = plan_wave(status, max_cells=2, modules=["gateway"])
    assert len(plan["targets"]) == 2


def test_plan_wave_area_priority() -> None:
    """영역 순위 G1 < G3 < G4 < G5 < G2 로 정렬."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G2-1", "status": "not_implemented"},
                    {"id": "G1-1", "status": "not_implemented"},
                    {"id": "G5-1", "status": "not_implemented"},
                    {"id": "G3-1", "status": "not_implemented"},
                    {"id": "G4-1", "status": "not_implemented"},
                ],
            }
        ]
    }
    plan = plan_wave(status, max_cells=5, modules=["gateway"])
    gates_ordered = [c["gate"] for c in plan["targets"]]
    assert gates_ordered == ["G1-1", "G3-1", "G4-1", "G5-1", "G2-1"]


def test_plan_wave_no_targets_means_no_approval() -> None:
    """모든 게이트 PASS 면 빈 wave · 승인 불요."""
    status = {"reports": [{"module": "gateway", "gates": [{"id": "G1-1", "status": "pass"}]}]}
    plan = plan_wave(status, max_cells=5, modules=["gateway"])
    assert plan["targets"] == []
    assert plan["requires_user_approval"] is False


def test_plan_wave_excludes_cells_with_unmet_dependencies() -> None:
    """의존 대상이 pass 가 아니면 해당 셀은 제외."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-2", "status": "not_implemented"},
                    {"id": "G1-5", "status": "not_implemented"},
                    {"id": "G3-1", "status": "not_implemented"},
                    {"id": "G3-2", "status": "not_implemented"},
                ],
            }
        ]
    }
    plan = plan_wave(
        status,
        max_cells=10,
        modules=["gateway"],
        dependencies={"G1-5": ["G1-2"], "G3-2": ["G3-1"]},
    )
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ("gateway", "G1-5") not in ids  # G1-2 미충족
    assert ("gateway", "G3-2") not in ids  # G3-1 미충족
    assert ("gateway", "G1-2") in ids  # 의존 없음
    assert ("gateway", "G3-1") in ids  # 의존 없음


def test_plan_wave_includes_cell_when_dependency_passed() -> None:
    """의존 대상이 pass 면 해당 셀 포함."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-2", "status": "pass"},
                    {"id": "G1-5", "status": "not_implemented"},
                ],
            }
        ]
    }
    plan = plan_wave(
        status,
        max_cells=10,
        modules=["gateway"],
        dependencies={"G1-5": ["G1-2"]},
    )
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ("gateway", "G1-5") in ids


def test_plan_wave_excludes_cells_requiring_excluded_tiers() -> None:
    """tier_map 에서 exclude_tiers 와 교집합이 있는 셀은 제외."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-2", "status": "not_implemented"},
                    {"id": "G4-3", "status": "not_implemented"},
                    {"id": "G5-3", "status": "not_implemented"},
                    {"id": "G2-5", "status": "not_implemented"},
                ],
            }
        ]
    }
    tier_map = {
        "G1-2": ["T1", "T2"],
        "G4-3": ["T3"],
        "G5-3": ["T2", "T3"],
        "G2-5": ["T1"],
    }
    plan = plan_wave(
        status,
        max_cells=10,
        modules=["gateway"],
        tier_map=tier_map,
        exclude_tiers=["T3"],
    )
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ("gateway", "G4-3") not in ids  # T3 전용 제외
    assert ("gateway", "G5-3") not in ids  # T2+T3 중 T3 포함 제외
    assert ("gateway", "G1-2") in ids  # T1+T2
    assert ("gateway", "G2-5") in ids  # T1
