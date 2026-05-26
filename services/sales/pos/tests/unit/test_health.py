"""POS 서비스 헬스 엔드포인트 테스트.

POS는 selling 서비스로 통합된 스텁이므로 app_factory가 제공하는
기본 헬스 엔드포인트만 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@patch("oneerp_core.health.get_client")
def test_startup_헬스체크_성공(
    mock_health_client: MagicMock,
    test_client: TestClient,
    mock_collection: None,
) -> None:
    """startup 프로브가 200을 반환하는지 확인한다."""
    mock_health_client.return_value.admin.command.return_value = {"ok": 1}
    response = test_client.get("/health/startup")
    assert response.status_code == 200


def test_live_헬스체크_성공(test_client: TestClient, mock_collection: None) -> None:
    """liveness 프로브가 200을 반환하는지 확인한다."""
    response = test_client.get("/health/live")
    assert response.status_code == 200


@patch("oneerp_core.health.get_client")
def test_ready_헬스체크_성공(
    mock_health_client: MagicMock,
    test_client: TestClient,
    mock_collection: None,
) -> None:
    """readiness 프로브가 200을 반환하는지 확인한다."""
    mock_health_client.return_value.admin.command.return_value = {"ok": 1}
    response = test_client.get("/health/ready")
    assert response.status_code == 200


def test_openapi_스키마_제공(test_client: TestClient, mock_collection: None) -> None:
    """OpenAPI 스키마 엔드포인트가 정상 동작하는지 확인한다."""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "OneERP Pos API"
