"""구독 서비스(SubscriptionService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_selling_app.services.subscription_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_selling_app.services.subscription_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_selling_app.services.subscription_service import SubscriptionService

        service = SubscriptionService(tenant_id="test-tenant")
    return (
        service,
        repos["subscription_plans"],
        repos["subscriptions"],
        repos["subscription_invoices"],
    )


class Test구독생성:
    def test_정상_생성(self) -> None:
        service, plan_repo, sub_repo, _inv = _make_service()
        plan_repo.find_by_id.return_value = {
            "_id": "SP-001",
            "billing_interval_days": 30,
            "amount": 99000,
        }

        result = service.create_subscription("CUST-001", "SP-001", date(2026, 4, 1))

        assert result["subscription_id"] == "SUB-001"
        assert result["amount"] == 99000
        sub_repo.insert.assert_called_once()

    def test_플랜_미존재_에러(self) -> None:
        service, plan_repo, _sub, _inv = _make_service()
        plan_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.create_subscription("CUST-001", "SP-999", date(2026, 4, 1))


class Test자동청구:
    def test_만기_구독_청구(self) -> None:
        service, plan_repo, sub_repo, inv_repo = _make_service()
        sub_repo.find_many.return_value = [
            {
                "_id": "SUB-001",
                "customer": "CUST-001",
                "plan": "SP-001",
                "amount": 99000,
                "next_billing_date": "2026-03-15",
                "status": "active",
            },
        ]
        plan_repo.find_by_id.return_value = {"billing_interval_days": 30}

        result = service.generate_invoices(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 1
        inv_repo.insert.assert_called_once()

    def test_미만기_구독_미청구(self) -> None:
        service, _plan, sub_repo, inv_repo = _make_service()
        sub_repo.find_many.return_value = [
            {
                "_id": "SUB-001",
                "next_billing_date": "2026-04-15",
                "status": "active",
            },
        ]

        result = service.generate_invoices(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 0
        inv_repo.insert.assert_not_called()


class Test구독해지:
    def test_해지(self) -> None:
        service, _plan, sub_repo, _inv = _make_service()
        sub_repo.find_by_id.return_value = {"_id": "SUB-001", "status": "active"}

        result = service.cancel_subscription("SUB-001", "서비스 불만")

        assert result["status"] == "cancelled"
        sub_repo.update_by_id.assert_called_once()
