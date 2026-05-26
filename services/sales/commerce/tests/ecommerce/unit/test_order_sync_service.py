"""마켓플레이스 주문 동기화 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_commerce_app.ecommerce.services.order_sync_service import OrderSyncService


@pytest.fixture
def mock_repos():
    """ecommerce_channels 및 marketplace_orders 컬렉션 mock을 설정한다."""
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


class Test주문동기화:
    """주문 동기화 시나리오."""

    def test_신규_주문_동기화_성공(self, mock_repos) -> None:
        """새로운 외부 주문이 마켓플레이스 주문으로 생성된다."""
        channel = {"_id": "ECH-0001", "is_active": True, "channel_name": "네이버"}
        mock_repos.find_one.return_value = channel
        mock_repos.find_one_and_update.return_value = channel
        # 중복 없음 — find().skip().limit() 체인 반환
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = iter([])
        mock_repos.find.return_value = mock_cursor

        svc = OrderSyncService(tenant_id="T001")
        result = svc.sync_orders(
            "ECH-0001",
            [
                {
                    "external_order_id": "EXT-001",
                    "customer_name": "홍길동",
                    "items": [{"item_code": "ITEM-A", "qty": 2}],
                    "total_amount": "50000",
                },
            ],
        )

        assert result["created"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == []

    def test_중복_주문_스킵(self, mock_repos) -> None:
        """이미 존재하는 외부 주문 ID는 건너뛴다."""
        channel = {"_id": "ECH-0001", "is_active": True}
        mock_repos.find_one.return_value = channel
        mock_repos.find_one_and_update.return_value = channel
        # 이미 존재 — find().skip().limit() 체인 반환
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = iter([{"_id": "MPO-0001"}])
        mock_repos.find.return_value = mock_cursor

        svc = OrderSyncService(tenant_id="T001")
        result = svc.sync_orders(
            "ECH-0001",
            [{"external_order_id": "EXT-001", "customer_name": "홍길동"}],
        )

        assert result["created"] == 0
        assert result["skipped"] == 1

    def test_비활성_채널_에러(self, mock_repos) -> None:
        """비활성 채널로 동기화 시 ValueError가 발생한다."""
        channel = {"_id": "ECH-0002", "is_active": False}
        mock_repos.find_one.return_value = channel
        mock_repos.find_one_and_update.return_value = channel

        svc = OrderSyncService(tenant_id="T001")
        with pytest.raises(ValueError, match="비활성 채널"):
            svc.sync_orders("ECH-0002", [])

    def test_미존재_채널_에러(self, mock_repos) -> None:
        """존재하지 않는 채널 ID로 동기화 시 ValueError가 발생한다."""
        mock_repos.find_one.return_value = None

        svc = OrderSyncService(tenant_id="T001")
        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.sync_orders("ECH-9999", [])


class Test주문확인:
    """주문 확인 시나리오."""

    def test_주문_확인_성공(self, mock_repos) -> None:
        """synced 상태 주문이 confirmed로 변경된다."""
        order = {"_id": "MPO-0001", "status": "synced"}
        mock_repos.find_one.return_value = order
        mock_repos.find_one_and_update.return_value = order

        svc = OrderSyncService(tenant_id="T001")
        result = svc.confirm_order("MPO-0001")

        assert result["status"] == "confirmed"
        mock_repos.update_one.assert_called()

    def test_이미_확인된_주문_에러(self, mock_repos) -> None:
        """synced가 아닌 상태의 주문은 확인할 수 없다."""
        order = {"_id": "MPO-0002", "status": "confirmed"}
        mock_repos.find_one.return_value = order
        mock_repos.find_one_and_update.return_value = order

        svc = OrderSyncService(tenant_id="T001")
        with pytest.raises(ValueError, match="확인 가능한 상태가 아닙니다"):
            svc.confirm_order("MPO-0002")

    def test_미존재_주문_에러(self, mock_repos) -> None:
        """존재하지 않는 주문 ID로 확인 시 ValueError가 발생한다."""
        mock_repos.find_one.return_value = None

        svc = OrderSyncService(tenant_id="T001")
        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.confirm_order("MPO-9999")
