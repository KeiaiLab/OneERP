"""ce-planner 가 호출 — 다음 wave 의 타겟 셀 선정."""

from __future__ import annotations

from datetime import UTC, datetime

_AREA_ORDER = {"G1": 0, "G3": 1, "G4": 2, "G5": 3, "G2": 4}


def _area(gate_id: str) -> str:
    return gate_id.split("-")[0]


def _gate_key(gate_id: str) -> tuple[int, int]:
    area, num = gate_id.split("-")
    return (_AREA_ORDER.get(area, 99), int(num))


def plan_wave(
    status: dict,
    *,
    max_cells: int = 10,
    modules: list[str] | None = None,
    dependencies: dict[str, list[str]] | None = None,
    tier_map: dict[str, list[str]] | None = None,
    exclude_tiers: list[str] | None = None,
) -> dict:
    """상태 JSON 에서 FAIL/NOT_IMPLEMENTED 셀을 영역·번호·모듈 순으로 정렬해 선택.

    영역 순위: G1 < G3 < G4 < G5 < G2 (스펙 §9 규약).
    dependencies: 특정 gate 가 다른 gate 의 PASS 를 선행 요구. 미충족 시 제외.
    tier_map + exclude_tiers: 요구 tier 에 exclude_tiers 와 교집합이 있으면 제외.
    """
    deps = dependencies or {}
    tiers = tier_map or {}
    excluded = set(exclude_tiers or [])

    # 모듈별 PASS 셀 집합 구축 (의존 체크용)
    passed: dict[str, set[str]] = {}
    for report in status.get("reports", []):
        module = report["module"]
        passed[module] = {g["id"] for g in report["gates"] if g["status"] == "pass"}

    candidates: list[dict[str, str]] = []
    for report in status.get("reports", []):
        module = report["module"]
        if modules and module not in modules:
            continue
        for gate in report["gates"]:
            if gate["status"] not in ("not_implemented", "fail"):
                continue
            required = deps.get(gate["id"], [])
            if required and not all(r in passed.get(module, set()) for r in required):
                continue
            if excluded and set(tiers.get(gate["id"], [])) & excluded:
                continue
            candidates.append({"module": module, "gate": gate["id"]})

    candidates.sort(key=lambda c: (_gate_key(c["gate"]), c["module"]))
    targets = candidates[:max_cells]

    return {
        "wave_id": datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ-w001"),
        "targets": targets,
        "preflight": "green",
        "requires_user_approval": bool(targets),
    }
