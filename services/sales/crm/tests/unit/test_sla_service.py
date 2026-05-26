"""SLAService 단위 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_crm_app.services.sla_service.generate_name",
        side_effect=lambda prefix, **kw: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """SLAService + mock 리포지터리를 생성한다."""
    with patch("oneerp_crm_app.services.sla_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_crm_app.services.sla_service import SLAService

        service = SLAService(tenant_id="test-tenant")
    return service, repos


class TestSLA평가:
    def test_이슈에_대한_SLA_평가(self) -> None:
        service, repos = _make_service()
        issue_repo = repos["issues"]
        sla_repo = repos["service_level_agreements"]
        fulfillment_repo = repos["sla_fulfillments"]

        issue_repo.find_by_id.return_value = {
            "_id": "ISS-001",
            "priority": "high",
            "status": "open",
            "created_at": datetime.now(tz=UTC) - timedelta(hours=1),
            "first_response_at": datetime.now(tz=UTC) - timedelta(minutes=30),
        }
        sla_repo.find_many.return_value = [
            {
                "_id": "SLA-001",
                "resolution_time": 4.0,
                "response_time": 2.0,
                "priority": "high",
                "is_active": True,
            }
        ]

        result = service.evaluate_sla("ISS-001")

        assert result["matched"] is True
        assert result["is_fulfilled"] is True
        assert result["sla_id"] == "SLA-001"
        assert result["response_breach"] is False
        assert result["resolution_breach"] is False
        fulfillment_repo.insert.assert_called_once()

    def test_응답시간_위반_시_미이행(self) -> None:
        """BR-CRM-004: response_time 초과 시 is_fulfilled=False."""
        service, repos = _make_service()
        created = datetime.now(tz=UTC) - timedelta(hours=1)
        repos["issues"].find_by_id.return_value = {
            "_id": "ISS-002",
            "priority": "critical",
            "status": "open",
            "created_at": created,
            # 첫 응답이 3시간 뒤 → response_time(1h) 초과
            "first_response_at": created + timedelta(hours=3),
        }
        repos["service_level_agreements"].find_many.return_value = [
            {
                "_id": "SLA-002",
                "resolution_time": 8.0,
                "response_time": 1.0,
                "priority": "critical",
                "is_active": True,
            }
        ]

        result = service.evaluate_sla("ISS-002")

        assert result["is_fulfilled"] is False
        assert result["response_breach"] is True
        assert result["resolution_breach"] is False

    def test_해결시간만_위반(self) -> None:
        """해결시간만 초과, 응답시간은 정상인 경우."""
        service, repos = _make_service()
        created = datetime.now(tz=UTC) - timedelta(hours=5)
        repos["issues"].find_by_id.return_value = {
            "_id": "ISS-003",
            "priority": "high",
            "status": "open",
            "created_at": created,
            "first_response_at": created + timedelta(minutes=10),
        }
        repos["service_level_agreements"].find_many.return_value = [
            {
                "_id": "SLA-003",
                "resolution_time": 4.0,
                "response_time": 1.0,
                "priority": "high",
                "is_active": True,
            }
        ]

        result = service.evaluate_sla("ISS-003")

        assert result["is_fulfilled"] is False
        assert result["response_breach"] is False
        assert result["resolution_breach"] is True

    def test_첫응답_없으면_현재시간_기준_응답시간_계산(self) -> None:
        """first_response_at 없으면 경과 시간으로 응답 위반 판정."""
        service, repos = _make_service()
        repos["issues"].find_by_id.return_value = {
            "_id": "ISS-004",
            "priority": "medium",
            "status": "open",
            "created_at": datetime.now(tz=UTC) - timedelta(hours=3),
            # first_response_at 없음
        }
        repos["service_level_agreements"].find_many.return_value = [
            {
                "_id": "SLA-004",
                "resolution_time": 8.0,
                "response_time": 1.0,
                "priority": "medium",
                "is_active": True,
            }
        ]

        result = service.evaluate_sla("ISS-004")

        # 3시간 경과, response_time=1h → 응답 위반
        assert result["response_breach"] is True
        assert result["is_fulfilled"] is False

    def test_매칭_SLA_없음(self) -> None:
        service, repos = _make_service()
        repos["issues"].find_by_id.return_value = {
            "_id": "ISS-001",
            "priority": "low",
            "status": "open",
            "created_at": datetime.now(tz=UTC),
        }
        repos["service_level_agreements"].find_many.return_value = []

        result = service.evaluate_sla("ISS-001")

        assert result["matched"] is False

    def test_존재하지_않는_엔티티_에러(self) -> None:
        service, repos = _make_service()
        repos["issues"].find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.evaluate_sla("ISS-999")


class TestSLA위반:
    def test_위반_건_조회(self) -> None:
        service, repos = _make_service()
        issue_repo = repos["issues"]
        sla_repo = repos["service_level_agreements"]

        # 2시간 전에 생성된 미해결 이슈, SLA 기한 1시간
        issue_repo.find_many.return_value = [
            {
                "_id": "ISS-001",
                "priority": "high",
                "status": "open",
                "created_at": datetime.now(tz=UTC) - timedelta(hours=2),
            }
        ]
        sla_repo.find_many.return_value = [{"_id": "SLA-001", "resolution_time": 1.0}]

        result = service.check_violations()

        assert result["total"] == 1
        assert result["violations"][0]["issue_id"] == "ISS-001"


class TestSLA이행률:
    def test_이행률_계산(self) -> None:
        service, repos = _make_service()
        repos["sla_fulfillments"].find_many.return_value = [
            {"is_fulfilled": True},
            {"is_fulfilled": True},
            {"is_fulfilled": False},
            {"is_fulfilled": True},
        ]

        result = service.get_fulfillment_rate()

        assert result["total"] == 4
        assert result["fulfilled"] == 3
        assert result["breached"] == 1
        assert result["fulfillment_rate"] == 75.0


class TestSLA에스컬레이션:
    def test_위반_에스컬레이션(self) -> None:
        service, repos = _make_service()
        repos["issues"].find_by_id.return_value = {
            "_id": "ISS-001",
            "priority": "critical",
            "status": "open",
        }

        result = service.escalate_breach("ISS-001", "response_time")

        assert result["escalated"] is True
        assert result["breach_type"] == "response_time"
        repos["issues"].update_by_id.assert_called_once()


class Test서비스계약유효기간:
    """BR-CRM-014: 서비스 계약 유효기간 검증 테스트."""

    def test_유효한_계약(self) -> None:
        """종료일이 오늘 이후이면 유효 상태를 반환한다."""
        service, repos = _make_service()
        future_date = (datetime.now(tz=UTC) + timedelta(days=30)).date()
        repos["service_contracts"].find_by_id.return_value = {
            "_id": "SC-001",
            "end_date": future_date,
            "is_active": True,
        }

        result = service.check_contract_validity("SC-001")

        assert result["is_expired"] is False
        assert result["is_active"] is True
        # 유효한 계약은 갱신하지 않음
        repos["service_contracts"].update_by_id.assert_not_called()

    def test_만료된_계약(self) -> None:
        """종료일이 오늘 이전이면 만료 상태를 반환하고 is_active를 False로 갱신한다."""
        service, repos = _make_service()
        past_date = (datetime.now(tz=UTC) - timedelta(days=1)).date()
        repos["service_contracts"].find_by_id.return_value = {
            "_id": "SC-002",
            "end_date": past_date,
            "is_active": True,
        }

        result = service.check_contract_validity("SC-002")

        assert result["is_expired"] is True
        assert result["is_active"] is False
        repos["service_contracts"].update_by_id.assert_called_once_with(
            "SC-002", {"is_active": False}
        )

    def test_존재하지_않는_계약_에러(self) -> None:
        service, repos = _make_service()
        repos["service_contracts"].find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.check_contract_validity("SC-999")

    def test_종료일_없는_계약_에러(self) -> None:
        """end_date가 없으면 에러를 발생시킨다."""
        service, repos = _make_service()
        repos["service_contracts"].find_by_id.return_value = {
            "_id": "SC-003",
            "end_date": None,
            "is_active": True,
        }

        with pytest.raises(OneERPError, match="ERR-CRM-014"):
            service.check_contract_validity("SC-003")
