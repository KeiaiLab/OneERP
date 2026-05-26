"""현장서비스(FieldServiceManager) 단위 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_crm_app.services.field_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_crm_app.services.field_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_crm_app.services.field_service import FieldServiceManager

        service = FieldServiceManager(tenant_id="test-tenant")
    return (
        service,
        repos["service_orders"],
        repos["service_visits"],
        repos["warranty_claims"],
        repos,
    )


class Test서비스오더:
    def test_오더_생성(self) -> None:
        service, order_repo, _visit, _claim, _repos = _make_service()
        result = service.create_service_order("CUST-001", "프린터 고장")
        assert result["order_id"] == "SVO-001"
        order_repo.insert.assert_called_once()

    def test_기술자_배정(self) -> None:
        service, order_repo, _visit, _claim, _repos = _make_service()
        order_repo.find_by_id.return_value = {"_id": "SVO-001", "status": "open"}

        result = service.assign_technician("SVO-001", "TECH-001")
        assert result["status"] == "assigned"


class Test서비스방문:
    def test_방문_기록(self) -> None:
        service, _order_repo, _visit_repo, _claim, _repos = _make_service()
        result = service.record_visit("SVO-001", "TECH-001", "부품 교체 완료")
        assert result["visit_id"] == "SVV-001"
        assert result["order_status"] == "resolved"


class Test보증클레임:
    def test_클레임_생성(self) -> None:
        service, _order, _visit, claim_repo, _repos = _make_service()
        result = service.create_warranty_claim("CUST-001", "ITEM-001", "불량")
        assert result["claim_id"] == "WC-001"
        claim_repo.insert.assert_called_once()


class Test보증기간검증:
    """BR-CRM-015: 보증 기간 검증 테스트."""

    def test_보증_기간_내(self) -> None:
        """구매일 기준 보증 기간 내이면 is_under_warranty=True를 반환한다."""
        service, _order, _visit, _claim, repos = _make_service()
        contract_repo = repos["service_contracts"]
        contract_repo.find_many.return_value = [
            {"item_code": "ITEM-001", "contract_type": "warranty", "warranty_months": 12}
        ]

        # 6개월 전 구매 → 12개월 보증 → 아직 유효
        purchase = datetime.now(tz=UTC).date() - timedelta(days=180)
        result = service.check_warranty("ITEM-001", purchase)

        assert result["is_under_warranty"] is True
        assert result["warranty_months"] == 12
        assert result["remaining_days"] > 0
        assert result["source"] == "service_contract"

    def test_보증_기간_만료(self) -> None:
        """보증 기간이 지났으면 is_under_warranty=False를 반환한다."""
        service, _order, _visit, _claim, repos = _make_service()
        contract_repo = repos["service_contracts"]
        contract_repo.find_many.return_value = [
            {"item_code": "ITEM-002", "contract_type": "warranty", "warranty_months": 6}
        ]

        # 1년 전 구매 → 6개월 보증 → 만료
        purchase = datetime.now(tz=UTC).date() - timedelta(days=365)
        result = service.check_warranty("ITEM-002", purchase)

        assert result["is_under_warranty"] is False
        assert result["remaining_days"] == 0

    def test_계약_없으면_클레임에서_조회(self) -> None:
        """서비스 계약이 없으면 warranty_claims에서 보증 기간을 조회한다."""
        service, _order, _visit, claim_repo, repos = _make_service()
        repos["service_contracts"].find_many.return_value = []
        claim_repo.find_many.return_value = [{"item_code": "ITEM-003", "warranty_months": 24}]

        purchase = datetime.now(tz=UTC).date() - timedelta(days=100)
        result = service.check_warranty("ITEM-003", purchase)

        assert result["source"] == "warranty_claim"
        assert result["warranty_months"] == 24
        assert result["is_under_warranty"] is True
