from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "verify_plane_boot.py"


@pytest.fixture(autouse=True)
def _plane_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONEERP_JWT_SECRET", "test-secret-for-plane-boot-000000")


def load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"검증 스크립트가 없습니다: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("verify_plane_boot", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("plane", ["realtime", "worker", "scheduler", "edge", "extension"])
def test_verify_plane_boot는_plane_인자로_비_api_plane을_검증할_수_있다(plane: str) -> None:
    module = load_module()

    exit_code = module.main(["--plane", plane])

    assert exit_code == 0


def test_verify_plane_boot는_catalog_정합성이_깨지면_실패한다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    monkeypatch.setattr(
        module,
        "load_plane_catalog",
        lambda root: {"api": object()},
    )

    exit_code = module.main(["--plane", "realtime"])

    assert exit_code == 1
