"""E2E 서비스 런처 회귀 테스트."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

from tests.e2e import conftest as e2e_conftest
from tests.e2e.helpers.api_client import HEADERS


def test_start_service가_uv_run_package로_서비스별_환경에서_기동한다(monkeypatch) -> None:
    """서비스 런처는 서비스별 uv package 환경에서 uvicorn을 기동한다."""
    captured: dict[str, object] = {}

    def fake_popen(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    e2e_conftest._start_service("selling", 8002)

    cmd = captured["args"][0]
    service_dir = Path(e2e_conftest.ROOT_DIR) / e2e_conftest.SERVICE_DIRS["selling"]

    assert cmd[:6] == [
        "uv",
        "run",
        "--package",
        "oneerp-selling",
        "--directory",
        str(service_dir),
    ]
    assert "uvicorn" in cmd
    assert captured["cwd"] == str(service_dir)
    assert captured["stdout"] is captured["stderr"]


def test_make_service_client가_기본_인증_헤더를_포함한다() -> None:
    client = e2e_conftest._make_service_client("http://127.0.0.1:8001")
    try:
        for key, value in HEADERS.items():
            assert client.headers[key] == value
    finally:
        client.close()
