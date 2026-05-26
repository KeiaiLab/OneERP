"""CLAUDE.md 전역 규칙 + ADR-0010 §2.1 buildx/linux-amd64 규약 컴플라이언스 테스트.

Ultraplan Step 1.2 — 각 plane Dockerfile 에 대해 `docker buildx build
--platform linux/amd64` 호출이 빌드 오케스트레이션에 존재해야 한다.
SoT: `scripts/build/build-planes.sh`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "check_buildx_compliance",
        ROOT / "scripts" / "ci" / "check_buildx_compliance.py",
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / "planes/api_plane").mkdir(parents=True)
    (tmp_path / "planes/worker_plane").mkdir(parents=True)
    (tmp_path / "planes/api_plane/Dockerfile").write_text("FROM python\n")
    (tmp_path / "planes/worker_plane/Dockerfile").write_text("FROM python\n")
    (tmp_path / "scripts/build").mkdir(parents=True)
    return tmp_path


def test_build_스크립트_부재시_FAIL(fake_repo: Path) -> None:
    mod = _load_module()
    result = mod.check(fake_repo)
    assert result.ok is False
    assert "build-planes.sh" in result.reason


def test_buildx_없는_스크립트는_FAIL(fake_repo: Path) -> None:
    (fake_repo / "scripts/build/build-planes.sh").write_text(
        "docker build -f planes/api_plane/Dockerfile .\n"
        "docker build -f planes/worker_plane/Dockerfile .\n",
    )
    mod = _load_module()
    result = mod.check(fake_repo)
    assert result.ok is False
    assert "buildx" in result.reason.lower() or "platform" in result.reason.lower()


def test_일부_plane만_커버하면_FAIL(fake_repo: Path) -> None:
    (fake_repo / "scripts/build/build-planes.sh").write_text(
        "docker buildx build --platform linux/amd64 -f planes/api_plane/Dockerfile .\n",
    )
    mod = _load_module()
    result = mod.check(fake_repo)
    assert result.ok is False
    assert "worker_plane" in result.reason


def test_전체_plane_buildx_linux_amd64_커버시_PASS(fake_repo: Path) -> None:
    (fake_repo / "scripts/build/build-planes.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "docker buildx build --platform linux/amd64 -f planes/api_plane/Dockerfile -t x .\n"
        "docker buildx build --platform linux/amd64 -f planes/worker_plane/Dockerfile -t y .\n",
    )
    mod = _load_module()
    result = mod.check(fake_repo)
    assert result.ok is True, result.reason


def test_멀티_아키텍처_플래그는_FAIL(fake_repo: Path) -> None:
    """CLAUDE.md '멀티아키텍처 빌드 금지' 규칙."""
    (fake_repo / "scripts/build/build-planes.sh").write_text(
        "docker buildx build --platform linux/amd64,linux/arm64 "
        "-f planes/api_plane/Dockerfile .\n"
        "docker buildx build --platform linux/amd64,linux/arm64 "
        "-f planes/worker_plane/Dockerfile .\n",
    )
    mod = _load_module()
    result = mod.check(fake_repo)
    assert result.ok is False
    assert "multi-arch" in result.reason.lower() or "arm64" in result.reason.lower()


def test_실제_레포에서_검사_실행가능하다() -> None:
    mod = _load_module()
    result = mod.check(ROOT)
    assert hasattr(result, "ok")
    assert hasattr(result, "reason")
