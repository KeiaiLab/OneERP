"""트리거 API 엔드포인트 테스트."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from oneerp_automation_orchestrator_app.main import app

_BASE_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "test-user",
}


def _make_client(permissions: str) -> TestClient:
    """권한 헤더를 포함한 테스트 클라이언트를 만든다."""
    test_client = TestClient(app)
    test_client.headers.update({**_BASE_HEADERS, "X-User-Permissions": permissions})
    return test_client


@pytest.fixture
def client() -> TestClient:
    """성공 케이스용 테스트 클라이언트를 반환한다."""
    return _make_client(
        "automation_definition:create,automation_run:create,automation_trigger:create,automation_schedule:create"
    )


def test_create_event_trigger(client: TestClient) -> None:
    """이벤트 트리거 생성 요청은 201을 반환해야 한다."""
    response = client.post(
        "/api/v1/automations/AUTO-T001-00001/triggers",
        json={"type": "event", "event_name": "approval_request.completed", "debounce_seconds": 5},
    )
    assert response.status_code == 201


def test_create_event_trigger_권한_없음_403() -> None:
    """권한이 없으면 트리거 생성이 거부된다."""
    client = _make_client("automation_definition:create")
    response = client.post(
        "/api/v1/automations/AUTO-T001-00001/triggers",
        json={"type": "event", "event_name": "approval_request.completed", "debounce_seconds": 5},
    )
    assert response.status_code == 403
