"""구독 라이프사이클 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_commerce_app.subscriptions.services.subscription_lifecycle_service import (
    SubscriptionLifecycleService,
)


@pytest.fixture
def mock_repos():
    """subscriptions, subscription_plans, subscription_invoices 컬렉션 mock을 설정한다."""
    with (
        patch("oneerp_core.repository.get_client") as mock_client,
        patch("oneerp_core.naming.get_client") as mock_naming_client,
    ):
        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "mock-id"
        mock_col.insert_one.return_value = mock_insert_result

        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_col.update_one.return_value = mock_update_result

        mock_naming_db = MagicMock()
        mock_naming_counters = MagicMock()
        mock_naming_db.__getitem__ = MagicMock(return_value=mock_naming_counters)
        mock_naming_client.return_value.__getitem__ = MagicMock(return_value=mock_naming_db)
        mock_naming_counters.find_one_and_update.return_value = {"seq": 1}

        yield mock_col


class Test구독활성화:
    """구독 활성화 시나리오."""

    def test_draft_구독_활성화_성공(self, mock_repos) -> None:
        """draft 상태 구독이 active로 전환되고 기간이 설정된다."""
        sub = {"_id": "SUB-0001", "status": "draft", "plan_id": "SPL-0001"}
        plan = {"_id": "SPL-0001", "billing_interval": "monthly", "price": "50000"}

        call_count = 0

        def _side_effect(query, *_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            doc_id = query.get("_id", "")
            if doc_id == "SUB-0001":
                return sub
            if doc_id == "SPL-0001":
                return plan
            return None

        mock_repos.find_one.side_effect = _side_effect
        mock_repos.find_one_and_update.side_effect = _side_effect

        svc = SubscriptionLifecycleService(tenant_id="T001")
        result = svc.activate("SUB-0001")

        assert result["status"] == "active"
        mock_repos.update_one.assert_called()

    def test_active_구독_재활성화_불가(self, mock_repos) -> None:
        """이미 active인 구독은 다시 활성화할 수 없다."""
        sub = {"_id": "SUB-0002", "status": "active", "plan_id": "SPL-0001"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        with pytest.raises(ValueError, match="불가"):
            svc.activate("SUB-0002")


class Test구독일시정지:
    """구독 일시정지 시나리오."""

    def test_active_구독_일시정지_성공(self, mock_repos) -> None:
        """active 상태 구독이 paused로 전환된다."""
        sub = {"_id": "SUB-0003", "status": "active"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        result = svc.pause("SUB-0003")

        assert result["status"] == "paused"

    def test_draft_구독_일시정지_불가(self, mock_repos) -> None:
        """draft 상태에서는 일시정지할 수 없다."""
        sub = {"_id": "SUB-0004", "status": "draft"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        with pytest.raises(ValueError, match="불가"):
            svc.pause("SUB-0004")


class Test구독해지:
    """구독 해지 시나리오."""

    def test_active_구독_해지_성공(self, mock_repos) -> None:
        """active 상태 구독이 cancelled로 전환되고 사유가 기록된다."""
        sub = {"_id": "SUB-0005", "status": "active"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        result = svc.cancel("SUB-0005", reason="더 이상 사용하지 않음")

        assert result["status"] == "cancelled"

    def test_미존재_구독_해지_에러(self, mock_repos) -> None:
        """존재하지 않는 구독 해지 시 ValueError가 발생한다."""
        mock_repos.find_one.return_value = None

        svc = SubscriptionLifecycleService(tenant_id="T001")
        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.cancel("SUB-9999")


class Test구독재개:
    """구독 재개 시나리오."""

    def test_paused_구독_재개_성공(self, mock_repos) -> None:
        """paused 상태 구독이 active로 복귀한다."""
        sub = {"_id": "SUB-0006", "status": "paused"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        result = svc.resume("SUB-0006")

        assert result["status"] == "active"


class Test청구생성:
    """구독 청구 생성 시나리오."""

    def test_청구서_생성_성공(self, mock_repos) -> None:
        """active 구독에서 청구서를 생성한다."""
        sub = {
            "_id": "SUB-0007",
            "status": "active",
            "plan_id": "SPL-0001",
            "current_period_start": "2026-03-01",
            "current_period_end": "2026-03-31",
            "company": "C001",
        }
        plan = {"_id": "SPL-0001", "price": "50000"}

        def _side_effect(query, *_args, **_kwargs):
            doc_id = query.get("_id", "")
            if doc_id == "SUB-0007":
                return sub
            if doc_id == "SPL-0001":
                return plan
            return None

        mock_repos.find_one.side_effect = _side_effect
        mock_repos.find_one_and_update.side_effect = _side_effect

        svc = SubscriptionLifecycleService(tenant_id="T001")
        result = svc.generate_invoice("SUB-0007")

        assert result["amount"] == "50000"
        assert result["status"] == "draft"
        assert result["invoice_id"].startswith("SINV-")
        mock_repos.insert_one.assert_called_once()

    def test_비활성_구독_청구_불가(self, mock_repos) -> None:
        """active가 아닌 구독에서는 청구서를 생성할 수 없다."""
        sub = {"_id": "SUB-0008", "status": "paused"}
        mock_repos.find_one.return_value = sub
        mock_repos.find_one_and_update.return_value = sub

        svc = SubscriptionLifecycleService(tenant_id="T001")
        with pytest.raises(ValueError, match="청구 생성 불가"):
            svc.generate_invoice("SUB-0008")
