"""CampaignExecutionService 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_marketing_automation_app.services.campaign_execution_service import (
    CampaignExecutionService,
)


@pytest.fixture
def mock_repos():
    """Mock Repository 인스턴스를 반환한다."""
    with patch(
        "oneerp_marketing_automation_app.services.campaign_execution_service.Repository"
    ) as mock_repo_cls:
        campaign_repo = MagicMock()
        analytics_repo = MagicMock()
        segment_repo = MagicMock()

        mock_repo_cls.side_effect = [campaign_repo, analytics_repo, segment_repo]

        yield {
            "campaign_repo": campaign_repo,
            "analytics_repo": analytics_repo,
            "segment_repo": segment_repo,
        }


@pytest.fixture
def service(mock_repos):
    """CampaignExecutionService 인스턴스를 반환한다."""
    return CampaignExecutionService(tenant_id="test-tenant")


class TestStartCampaign:
    """캠페인 시작 테스트."""

    def test_캠페인_시작_성공(self, service, mock_repos) -> None:
        """draft 캠페인을 시작하면 running 상태가 된다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00001",
            "campaign_name": "봄 프로모션",
            "status": "draft",
            "target_audience_id": "SEG-001",
        }
        mock_repos["segment_repo"].find_by_id.return_value = {
            "_id": "SEG-001",
            "member_count": 5000,
        }

        result = service.start_campaign("MKC-00001")

        assert result["status"] == "running"
        assert result["audience_count"] == 5000
        mock_repos["campaign_repo"].update_by_id.assert_called_once()

    def test_미존재_캠페인_에러(self, service, mock_repos) -> None:
        """존재하지 않는 캠페인이면 ValueError가 발생한다."""
        mock_repos["campaign_repo"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="캠페인을 찾을 수 없습니다"):
            service.start_campaign("MKC-99999")

    def test_완료된_캠페인_시작불가(self, service, mock_repos) -> None:
        """completed 상태 캠페인은 시작할 수 없다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00002",
            "status": "completed",
        }

        with pytest.raises(ValueError, match="시작할 수 없는 상태"):
            service.start_campaign("MKC-00002")


class TestPauseCampaign:
    """캠페인 일시정지 테스트."""

    def test_일시정지_성공(self, service, mock_repos) -> None:
        """running 캠페인을 일시정지하면 paused 상태가 된다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00001",
            "status": "running",
        }

        result = service.pause_campaign("MKC-00001")

        assert result["status"] == "paused"

    def test_draft_캠페인_일시정지_불가(self, service, mock_repos) -> None:
        """draft 상태 캠페인은 일시정지할 수 없다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00002",
            "status": "draft",
        }

        with pytest.raises(ValueError, match="일시정지할 수 없는 상태"):
            service.pause_campaign("MKC-00002")


class TestCompleteCampaign:
    """캠페인 완료 테스트."""

    def test_완료_성공_지표집계(self, service, mock_repos) -> None:
        """running 캠페인을 완료하면 지표가 집계된다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00001",
            "status": "running",
        }
        mock_repos["analytics_repo"].find_many.return_value = [
            {"event_type": "impression", "revenue_attributed": 0},
            {"event_type": "click", "revenue_attributed": 0},
            {"event_type": "conversion", "revenue_attributed": 50000},
        ]

        result = service.complete_campaign("MKC-00001")

        assert result["status"] == "completed"
        assert result["metrics"]["conversions"] == 1
        assert result["metrics"]["impressions"] == 1


class TestCampaignROI:
    """캠페인 ROI 계산 테스트."""

    def test_ROI_계산(self, service, mock_repos) -> None:
        """budget/spent/revenue 기반으로 ROI를 계산한다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00001",
            "budget": 1000000,
            "spent": 500000,
        }
        mock_repos["analytics_repo"].find_many.return_value = [
            {"event_type": "conversion", "revenue_attributed": 400000},
            {"event_type": "conversion", "revenue_attributed": 600000},
        ]

        result = service.get_campaign_roi("MKC-00001")

        assert float(result["total_revenue"]) == 1000000.0
        # ROI = (1000000 - 500000) / 500000 * 100 = 100%
        assert float(result["roi_percent"]) == 100.00

    def test_지출_없을때_ROI_0(self, service, mock_repos) -> None:
        """지출이 0이면 ROI는 0이다."""
        mock_repos["campaign_repo"].find_by_id.return_value = {
            "_id": "MKC-00002",
            "budget": 1000000,
            "spent": 0,
        }
        mock_repos["analytics_repo"].find_many.return_value = []

        result = service.get_campaign_roi("MKC-00002")

        assert float(result["roi_percent"]) == 0
