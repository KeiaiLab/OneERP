"""ComplianceService 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_gtm_app.services.compliance_service import ComplianceService


@pytest.fixture
def mock_repos():
    """Mock Repository 인스턴스를 반환한다."""
    with patch("oneerp_gtm_app.services.compliance_service.Repository") as mock_repo_cls:
        check_repo = MagicMock()
        agreement_repo = MagicMock()
        hs_repo = MagicMock()

        mock_repo_cls.side_effect = [check_repo, agreement_repo, hs_repo]

        yield {
            "check_repo": check_repo,
            "agreement_repo": agreement_repo,
            "hs_repo": hs_repo,
        }


@pytest.fixture
def service(mock_repos):
    """ComplianceService 인스턴스를 반환한다."""
    return ComplianceService(tenant_id="test-tenant")


class TestScreenEntity:
    """거래 상대방 스크리닝 테스트."""

    def test_스크리닝_패스(self, service, mock_repos) -> None:
        """매칭되는 제재 기록이 없으면 pass를 반환한다."""
        mock_repos["check_repo"].find_many.return_value = []

        result = service.screen_entity("TestCorp", "US")

        assert result["result"] == "pass"
        assert result["risk_level"] == "low"
        assert result["entity_name"] == "TestCorp"

    def test_스크리닝_실패_고위험(self, service, mock_repos) -> None:
        """denied_party + sanction에 매칭되면 high 이상이 된다."""

        def side_effect(query, limit=1):
            check_type = query.get("check_type", "")
            if check_type in ("denied_party", "sanction"):
                return [{"result": "fail"}]
            return []

        mock_repos["check_repo"].find_many.side_effect = side_effect

        result = service.screen_entity("BadCorp", "IR")

        assert result["result"] == "fail"
        assert result["risk_level"] in ("high", "critical")

    def test_특정_점검유형만_실행(self, service, mock_repos) -> None:
        """check_types를 지정하면 해당 유형만 점검한다."""
        mock_repos["check_repo"].find_many.return_value = []

        result = service.screen_entity("TestCorp", "US", check_types=["embargo"])

        assert len(result["details"]) == 1
        assert result["details"][0]["check_type"] == "embargo"


class TestExportEligibility:
    """수출 적격성 확인 테스트."""

    def test_HS분류_없으면_부적격(self, service, mock_repos) -> None:
        """HS 분류가 없는 품목은 수출 부적격이다."""
        mock_repos["hs_repo"].find_many.return_value = []

        result = service.check_export_eligibility("ITEM-001", "JP")

        assert result["eligible"] is False
        assert "HS 분류 정보가 없습니다" in result["reason"]

    def test_HS분류_있고_협정_매칭(self, service, mock_repos) -> None:
        """HS 분류가 있고 대상국 협정이 있으면 적격 + 협정 정보를 반환한다."""
        mock_repos["hs_repo"].find_many.return_value = [
            {
                "item_code": "ITEM-001",
                "hs_code": "8471.30",
                "duty_rate": 8,
                "preferential_rate": 0,
            },
        ]
        mock_repos["agreement_repo"].find_many.return_value = [
            {
                "agreement_code": "KR-JP-EPA",
                "agreement_name": "한일 경제동반자협정",
                "agreement_type": "EPA",
                "country_codes": ["JP"],
            },
            {
                "agreement_code": "RCEP",
                "agreement_name": "역내포괄적경제동반자협정",
                "agreement_type": "RCEP",
                "country_codes": ["JP", "CN", "AU"],
            },
        ]

        result = service.check_export_eligibility("ITEM-001", "JP")

        assert result["eligible"] is True
        assert result["hs_code"] == "8471.30"
        assert len(result["agreements"]) == 2

    def test_HS분류_있고_협정_미매칭(self, service, mock_repos) -> None:
        """HS 분류가 있지만 대상국 협정이 없으면 적격이지만 협정은 빈 목록이다."""
        mock_repos["hs_repo"].find_many.return_value = [
            {"item_code": "ITEM-002", "hs_code": "2710.12", "duty_rate": 5},
        ]
        mock_repos["agreement_repo"].find_many.return_value = [
            {
                "agreement_code": "KR-US-FTA",
                "agreement_name": "한미 FTA",
                "country_codes": ["US"],
            },
        ]

        result = service.check_export_eligibility("ITEM-002", "RU")

        assert result["eligible"] is True
        assert len(result["agreements"]) == 0
