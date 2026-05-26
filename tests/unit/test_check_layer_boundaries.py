from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "dev" / "check_layer_boundaries.py"
BASELINE_PATH = ROOT / ".arch-baseline.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_layer_boundaries", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_새_규칙_id가_RULES와_baseline에_포함된다() -> None:
    module = _load_module()

    rule_counts = module.build_report().count_by_rule()
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    assert "OE101-plane-domain-rule-leak" in rule_counts
    assert "OE201-web-contract-bypass" in rule_counts
    assert "OE101-plane-domain-rule-leak" in baseline
    assert "OE201-web-contract-bypass" in baseline


def test_oe101_패턴이_plane_조립_코드를_오탐하지_않는다() -> None:
    """OE101 패턴이 실제 도메인 enum/상수는 감지하고, 조립 코드는 오탐하지 않는다."""
    module = _load_module()
    pattern = module.RULES["OE101-plane-domain-rule-leak"]["pattern"]
    # 감지해야 하는 케이스 — plane 내 도메인 enum 직접 정의
    assert pattern.search("class InvoiceStatus(str, Enum):"), "도메인 enum 감지 실패"
    assert pattern.search("class OrderType(Enum):"), "도메인 enum 감지 실패"
    assert pattern.search("class PaymentState(int, Enum):"), "도메인 enum 감지 실패"
    # 오탐하면 안 되는 케이스 — 조립 코드의 일반 로직
    assert not pattern.search("    if legacy_app_count > 1:"), "plane 조립 코드 오탐"
    assert not pattern.search('raise ValueError("최소 1개 도메인 마운트 필요")'), (
        "plane 조립 코드 오탐"
    )


def test_glob이_oneerp_app_구조를_인식한다() -> None:
    """현재 서비스 구조는 services/<도메인>/<서비스>/oneerp_<이름>_app/... 이다."""
    cblm = _load_module()

    assert "oneerp_" in cblm.ROUTES_GLOB, (
        f"ROUTES_GLOB가 oneerp_*_app 구조를 반영해야 함: {cblm.ROUTES_GLOB}"
    )
    assert "oneerp_" in cblm.MODELS_GLOB, (
        f"MODELS_GLOB가 oneerp_*_app 구조를 반영해야 함: {cblm.MODELS_GLOB}"
    )
