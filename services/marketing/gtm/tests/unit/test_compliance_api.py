"""준수점검 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_gtm_app.main import app as gtm_app

# 테스트용 인증 헤더
_AUTH_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "test-user",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}

client = TestClient(gtm_app)


def test_스크리닝_API_정상() -> None:
    """POST /api/v1/gtm/compliance/screen — 스크리닝 실행 시 200."""
    mock_result = {
        "entity_name": "TestCorp",
        "entity_country": "US",
        "result": "pass",
        "risk_level": "low",
        "total_score": 0,
        "details": [],
    }

    with patch("oneerp_gtm_app.routes.compliance.ComplianceService") as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.screen_entity.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/gtm/compliance/screen",
            params={"entity_name": "TestCorp", "entity_country": "US"},
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "pass"


def test_수출적격성_API_정상() -> None:
    """GET /api/v1/gtm/compliance/export-eligibility — 적격성 확인 시 200."""
    mock_result = {
        "item_code": "ITEM-001",
        "destination_country": "JP",
        "eligible": True,
        "hs_code": "8471.30",
        "agreements": [],
    }

    with patch("oneerp_gtm_app.routes.compliance.ComplianceService") as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.check_export_eligibility.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.get(
            "/api/v1/gtm/compliance/export-eligibility",
            params={"item_code": "ITEM-001", "destination_country": "JP"},
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is True
