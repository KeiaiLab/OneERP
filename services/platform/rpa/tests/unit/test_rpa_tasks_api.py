"""RPA 작업 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_rpa_app.routes.rpa_tasks as _tasks_mod
from fastapi.testclient import TestClient
from oneerp_rpa_app.main import app as rpa_app

client = TestClient(rpa_app)


def _mock_repo() -> MagicMock:
    """공통 Repository mock을 반환한다."""
    return MagicMock()


# --- 작업 생성 ---


def test_작업_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/rpa/tasks — 유효한 task_type으로 작업 생성 시 201."""
    repo = _mock_repo()
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_tasks_mod, "generate_name", lambda prefix, **_: "RPAT-2026-00001")  # type: ignore[attr-defined]

    resp = client.post(
        "/api/v1/rpa/tasks/",
        json={
            "task_type": "hometax_issue",
            "input_data": {"cert_password": "test1234"},
            "device_id": "emulator-5554",
            "priority": 0,
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["task_id"] == "RPAT-2026-00001"


def test_작업_생성_잘못된_task_type(monkeypatch: object) -> None:
    """POST /api/v1/rpa/tasks — 유효하지 않은 task_type이면 400."""
    repo = _mock_repo()
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.post(
        "/api/v1/rpa/tasks/",
        json={"task_type": "invalid_type", "input_data": {}},
    )

    assert resp.status_code == 400


# --- 목록 조회 ---


def test_작업_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/rpa/tasks — 목록 조회 시 200."""
    repo = _mock_repo()
    repo.find_many.return_value = [
        {"_id": "RPAT-00001", "task_type": "hometax_issue", "status": "pending"},
    ]
    repo.count.return_value = 1
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.get("/api/v1/rpa/tasks/")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "items" in data


# --- 상세 조회 ---


def test_작업_상세_조회(monkeypatch: object) -> None:
    """GET /api/v1/rpa/tasks/{id} — 존재하는 작업 조회 시 200."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {
        "_id": "RPAT-00001",
        "task_type": "hometax_issue",
        "status": "pending",
    }
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.get("/api/v1/rpa/tasks/RPAT-00001")

    assert resp.status_code == 200


def test_작업_상세_조회_미존재(monkeypatch: object) -> None:
    """GET /api/v1/rpa/tasks/{id} — 존재하지 않는 작업이면 404."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.get("/api/v1/rpa/tasks/RPAT-99999")

    assert resp.status_code == 404


# --- 기기 목록 ---


def test_기기_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/rpa/tasks/devices — 기기 목록 조회 시 200."""
    monkeypatch.setattr(  # type: ignore[attr-defined]
        _tasks_mod,
        "_appium_manager",
        type(
            "_FakeAppium",
            (),
            {
                "get_connected_devices": staticmethod(
                    lambda: [{"id": "emulator-5554", "status": "connected"}],
                ),
            },
        )(),
    )

    resp = client.get("/api/v1/rpa/tasks/devices")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


# --- 작업 실행 ---


def test_작업_실행_요청(monkeypatch: object) -> None:
    """POST /api/v1/rpa/tasks/{id}/run — pending 작업 실행 시 200."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {
        "_id": "RPAT-00001",
        "task_type": "hometax_issue",
        "status": "pending",
    }
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.post("/api/v1/rpa/tasks/RPAT-00001/run")

    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "RPAT-00001"


def test_실행_불가_상태(monkeypatch: object) -> None:
    """POST /api/v1/rpa/tasks/{id}/run — running 상태이면 400."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {
        "_id": "RPAT-00001",
        "task_type": "hometax_issue",
        "status": "running",
    }
    monkeypatch.setattr(_tasks_mod, "_get_repo", lambda tenant_id="": repo)  # type: ignore[attr-defined]

    resp = client.post("/api/v1/rpa/tasks/RPAT-00001/run")

    assert resp.status_code == 400
