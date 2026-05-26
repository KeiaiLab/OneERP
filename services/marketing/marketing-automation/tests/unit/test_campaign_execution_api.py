"""캠페인 실행 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_marketing_automation_app.main import app as marketing_app

# 테스트용 인증 헤더
_AUTH_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "test-user",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}

client = TestClient(marketing_app)


def test_캠페인_시작_API_정상() -> None:
    """POST /api/v1/marketing/campaigns/{id}/start — 캠페인 시작 시 200."""
    with patch(
        "oneerp_marketing_automation_app.routes.campaign_execution.CampaignExecutionService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.start_campaign.return_value = {
            "campaign_id": "MKC-00001",
            "status": "running",
            "audience_count": 5000,
        }
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/marketing/campaigns/MKC-00001/start",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_캠페인_일시정지_API_정상() -> None:
    """POST /api/v1/marketing/campaigns/{id}/pause — 일시정지 시 200."""
    with patch(
        "oneerp_marketing_automation_app.routes.campaign_execution.CampaignExecutionService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.pause_campaign.return_value = {
            "campaign_id": "MKC-00001",
            "status": "paused",
        }
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/marketing/campaigns/MKC-00001/pause",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_캠페인_ROI_API_정상() -> None:
    """GET /api/v1/marketing/campaigns/{id}/roi — ROI 조회 시 200."""
    with patch(
        "oneerp_marketing_automation_app.routes.campaign_execution.CampaignExecutionService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.get_campaign_roi.return_value = {
            "campaign_id": "MKC-00001",
            "budget": 1000000,
            "spent": 500000,
            "total_revenue": 1000000,
            "roi_percent": 100.0,
        }
        mock_svc_cls.return_value = mock_svc

        resp = client.get(
            "/api/v1/marketing/campaigns/MKC-00001/roi",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json()["roi_percent"] == 100.0
