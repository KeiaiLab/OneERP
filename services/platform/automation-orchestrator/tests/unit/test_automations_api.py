"""자동화 정의 API 엔드포인트 테스트."""

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
    return _make_client("automation_definition:create,automation_run:create")


def test_create_automation(client: TestClient) -> None:
    """자동화 정의 생성 시 최소 응답 계약을 반환한다."""
    response = client.post("/api/v1/automations", json={"name": "지급 후처리"})
    assert response.status_code == 201
    body = response.json()
    assert body["automation_id"].startswith("AUTO-STUB-")
    assert body["version"] == 1
    assert body["status"] == "draft"


def test_create_automation_권한_없음_403() -> None:
    """권한이 없으면 자동화 정의 생성이 거부된다."""
    client = _make_client("automation_definition:read")
    response = client.post("/api/v1/automations", json={"name": "지급 후처리"})
    assert response.status_code == 403
