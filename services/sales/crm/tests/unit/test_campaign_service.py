"""마케팅 캠페인 서비스(CampaignService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_crm_app.services.campaign_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_crm_app.services.campaign_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_crm_app.services.campaign_service import CampaignService

        service = CampaignService(tenant_id="test-tenant")
    return service, repos["email_campaigns"], repos["marketing_lists"], repos


class Test캠페인생성:
    def test_이메일_캠페인_생성(self) -> None:
        service, email_repo, list_repo, _repos = _make_service()
        list_repo.find_by_id.return_value = {"_id": "ML-001", "members": ["C1", "C2", "C3"]}

        result = service.create_campaign("email", "봄 세일", "ML-001", "할인 안내")

        assert result["campaign_id"] == "EC-001"
        assert result["recipient_count"] == 3
        email_repo.insert.assert_called_once()

    def test_리스트_미존재_에러(self) -> None:
        service, _email, list_repo, _repos = _make_service()
        list_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.create_campaign("email", "테스트", "ML-999", "내용")


class TestROI:
    def test_ROI_계산(self) -> None:
        service, email_repo, _list, _repos = _make_service()
        email_repo.find_by_id.return_value = {
            "_id": "EC-001",
            "sent_count": 1000,
            "open_count": 300,
            "click_count": 50,
            "revenue": 5000000,
            "cost": 1000000,
        }

        result = service.calculate_roi("EC-001")

        assert result["open_rate"] == 30.0
        # BR-CRM-007: 클릭률 = clicked / opened * 100 = 50/300*100
        assert result["click_rate"] == 16.67
        assert result["roi"] == 400.0  # (5M-1M)/1M * 100

    def test_오픈_0일_때_클릭률_0(self) -> None:
        """오픈 수가 0이면 클릭률은 0.0을 반환한다."""
        service, email_repo, _list, _repos = _make_service()
        email_repo.find_by_id.return_value = {
            "_id": "EC-002",
            "sent_count": 100,
            "open_count": 0,
            "click_count": 0,
            "revenue": 0,
            "cost": 500000,
        }

        result = service.calculate_roi("EC-002")

        assert result["click_rate"] == 0.0
        assert result["open_rate"] == 0.0


class Test로열티포인트적립:
    """BR-CRM-020: 로열티 포인트 적립 테스트."""

    def test_포인트_적립(self) -> None:
        """고객에게 포인트를 적립한다."""
        service, _email, _list, repos = _make_service()
        loyalty_repo = repos["loyalty_points"]
        loyalty_repo.find_many.return_value = [{"balance": 100}]

        result = service.award_points("CUST-001", 50, "구매 적립")

        assert result["customer_id"] == "CUST-001"
        assert result["points_earned"] == 50
        assert result["balance"] == 150
        loyalty_repo.insert.assert_called_once()

    def test_첫_적립_잔액_없음(self) -> None:
        """기존 포인트가 없는 고객 첫 적립."""
        service, _email, _list, repos = _make_service()
        repos["loyalty_points"].find_many.return_value = []

        result = service.award_points("CUST-NEW", 100, "신규 가입")

        assert result["balance"] == 100

    def test_적립_0이하_에러(self) -> None:
        """적립 포인트가 0 이하이면 에러를 발생시킨다."""
        service, _email, _list, _repos = _make_service()

        with pytest.raises(OneERPError, match="ERR-CRM-020"):
            service.award_points("CUST-001", 0)


class Test로열티포인트차감:
    """BR-CRM-020: 로열티 포인트 차감 테스트."""

    def test_포인트_차감(self) -> None:
        """잔액이 충분하면 차감에 성공한다."""
        service, _email, _list, repos = _make_service()
        repos["loyalty_points"].find_many.return_value = [{"balance": 200}]

        result = service.redeem_points("CUST-001", 80)

        assert result["points_redeemed"] == 80
        assert result["balance"] == 120

    def test_잔액_부족_에러(self) -> None:
        """잔액이 부족하면 에러를 발생시킨다."""
        service, _email, _list, repos = _make_service()
        repos["loyalty_points"].find_many.return_value = [{"balance": 30}]

        with pytest.raises(OneERPError, match="ERR-CRM-020"):
            service.redeem_points("CUST-001", 50)

    def test_포인트_내역_없는_고객_에러(self) -> None:
        """포인트 내역이 없는 고객 차감 시 에러."""
        service, _email, _list, repos = _make_service()
        repos["loyalty_points"].find_many.return_value = []

        with pytest.raises(OneERPError, match="ERR-CRM-020"):
            service.redeem_points("CUST-999", 10)
