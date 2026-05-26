"""캠페인 발송 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_marketing_app.services.campaign_service import CampaignService


@pytest.fixture
def mock_repos():
    """email_campaigns, sms_campaigns, marketing_lists 컬렉션 mock을 설정한다."""
    with (
        patch("oneerp_core.repository.get_client") as mock_client,
        patch("oneerp_core.naming.get_client") as mock_naming_client,
    ):
        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_col.update_one.return_value = mock_update_result

        mock_naming_db = MagicMock()
        mock_naming_counters = MagicMock()
        mock_naming_db.__getitem__ = MagicMock(return_value=mock_naming_counters)
        mock_naming_client.return_value.__getitem__ = MagicMock(return_value=mock_naming_db)
        mock_naming_counters.find_one_and_update.return_value = {"seq": 1}

        yield mock_col


class Test이메일캠페인발송:
    """이메일 캠페인 발송 시나리오."""

    def test_이메일_캠페인_발송_성공(self, mock_repos) -> None:
        """draft 상태 이메일 캠페인이 발송되고 sent_count가 기록된다."""
        campaign = {
            "_id": "EC-0001",
            "status": "draft",
            "marketing_list_id": "ML-0001",
            "subject": "프로모션 안내",
        }
        mkt_list = {
            "_id": "ML-0001",
            "members": [
                {"email": "user1@example.com", "opt_in": True},
                {"email": "user2@example.com", "opt_in": True},
                {"email": "", "opt_in": True},  # 이메일 없음 — 제외
                {"email": "user3@example.com", "opt_in": False},  # 수신거부 — 제외
            ],
        }

        def _find_one_side_effect(query, *_args, **_kwargs):
            doc_id = query.get("_id", "")
            if doc_id == "EC-0001":
                return campaign
            if doc_id == "ML-0001":
                return mkt_list
            return None

        mock_repos.find_one.side_effect = _find_one_side_effect
        mock_repos.find_one_and_update.side_effect = _find_one_side_effect

        svc = CampaignService(tenant_id="T001")
        result = svc.send_email_campaign("EC-0001")

        assert result["status"] == "sent"
        assert result["sent_count"] == 2
        mock_repos.update_one.assert_called()

    def test_이미_발송된_캠페인_에러(self, mock_repos) -> None:
        """sent 상태 캠페인은 재발송할 수 없다."""
        campaign = {"_id": "EC-0002", "status": "sent"}
        mock_repos.find_one.return_value = campaign
        mock_repos.find_one_and_update.return_value = campaign

        svc = CampaignService(tenant_id="T001")
        with pytest.raises(ValueError, match="발송 가능한 상태가 아닙니다"):
            svc.send_email_campaign("EC-0002")

    def test_미존재_캠페인_에러(self, mock_repos) -> None:
        """존재하지 않는 캠페인 ID로 발송 시 ValueError가 발생한다."""
        mock_repos.find_one.return_value = None

        svc = CampaignService(tenant_id="T001")
        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.send_email_campaign("EC-9999")

    def test_미존재_마케팅_목록_에러(self, mock_repos) -> None:
        """캠페인의 마케팅 목록이 없으면 ValueError가 발생한다."""
        campaign = {
            "_id": "EC-0003",
            "status": "draft",
            "marketing_list_id": "ML-9999",
        }

        call_count = 0

        def _side_effect(query, *_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return campaign
            return None

        mock_repos.find_one.side_effect = _side_effect
        mock_repos.find_one_and_update.side_effect = _side_effect

        svc = CampaignService(tenant_id="T001")
        with pytest.raises(ValueError, match="마케팅 목록"):
            svc.send_email_campaign("EC-0003")


class TestSMS캠페인발송:
    """SMS 캠페인 발송 시나리오."""

    def test_SMS_캠페인_발송_성공(self, mock_repos) -> None:
        """draft 상태 SMS 캠페인이 발송된다."""
        campaign = {
            "_id": "SC-0001",
            "status": "draft",
            "marketing_list_id": "ML-0001",
            "message": "프로모션 안내",
        }
        mkt_list = {
            "_id": "ML-0001",
            "members": [
                {"phone": "010-1234-5678", "opt_in": True},
                {"phone": "010-9876-5432", "opt_in": True},
            ],
        }

        def _find_one_side_effect(query, *_args, **_kwargs):
            doc_id = query.get("_id", "")
            if doc_id == "SC-0001":
                return campaign
            if doc_id == "ML-0001":
                return mkt_list
            return None

        mock_repos.find_one.side_effect = _find_one_side_effect
        mock_repos.find_one_and_update.side_effect = _find_one_side_effect

        svc = CampaignService(tenant_id="T001")
        result = svc.send_sms_campaign("SC-0001")

        assert result["status"] == "sent"
        assert result["sent_count"] == 2

    def test_미존재_SMS_캠페인_에러(self, mock_repos) -> None:
        """존재하지 않는 SMS 캠페인 ID로 발송 시 ValueError가 발생한다."""
        mock_repos.find_one.return_value = None

        svc = CampaignService(tenant_id="T001")
        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.send_sms_campaign("SC-9999")
