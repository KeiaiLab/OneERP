"""통합 플로우 실행 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_integration_hub_app.main import app as hub_app

# 테스트용 인증 헤더
_AUTH_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "test-user",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}

client = TestClient(hub_app)


def test_플로우_실행_API_정상() -> None:
    """POST /api/v1/integration/flows/{id}/execute — 플로우 실행 시 200."""
    mock_result = {
        "flow_id": "IFLOW-00001",
        "status": "success",
        "records_processed": 100,
        "records_failed": 0,
        "duration_ms": 500,
    }

    with patch(
        "oneerp_integration_hub_app.routes.flow_execution.FlowExecutorService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.execute_flow.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/integration/flows/IFLOW-00001/execute",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_데이터_변환_API_정상() -> None:
    """POST /api/v1/integration/flows/transform — 데이터 변환 시 200."""
    mock_result = {
        "transformed_data": [{"company_name": "테스트"}],
        "total": 1,
        "success": 1,
        "failed": 0,
    }

    with patch(
        "oneerp_integration_hub_app.routes.flow_execution.FlowExecutorService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.transform_data.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/integration/flows/transform",
            json={
                "mapping_id": "DMAP-001",
                "source_data": [{"name": "테스트"}],
            },
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] == 1
