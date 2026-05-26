"""E2E 서비스 런처 회귀 테스트."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

from tests.e2e import conftest as e2e_conftest


def test_start_service_로그_파이프를_사용하지_않는다(monkeypatch) -> None:
    """서비스 런처는 파이프 버퍼로 인해 기동이 멈추지 않도록 stdout/stderr를 버린다."""
    captured: dict[str, object] = {}

    def fake_popen(*args, **kwargs):
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    e2e_conftest._start_service("selling", 8002)

    assert captured["stdout"] is subprocess.DEVNULL
    assert captured["stderr"] is subprocess.DEVNULL
