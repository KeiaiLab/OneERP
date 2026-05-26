"""포괄주문 서비스(BlanketOrderService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    with (
        patch("oneerp_selling_app.services.blanket_order_service.Repository") as mock_repo_cls,
        patch(
            "oneerp_selling_app.services.blanket_order_service.generate_name",
            return_value="SO-2026-00001",
        ) as mock_name,
    ):
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_selling_app.services.blanket_order_service import BlanketOrderService

        service = BlanketOrderService(tenant_id="test-tenant")
    return service, repos["blanket_orders"], repos["sales_orders"], mock_name


def _sample_blo() -> dict:
    return {
        "_id": "BLO-001",
        "customer": "CUST-001",
        "items": [
            {"item_code": "ITEM-001", "qty": 1000, "rate": 100, "ordered_qty": 200},
            {"item_code": "ITEM-002", "qty": 500, "rate": 50, "ordered_qty": 0},
        ],
    }


class Test분할주문:
    def test_정상_분할주문(self) -> None:
        service, blo_repo, _so_repo, _mock_name = _make_service()
        blo_repo.find_by_id.return_value = _sample_blo()

        with patch(
            "oneerp_selling_app.services.blanket_order_service.generate_name",
            return_value="SO-2026-00001",
        ):
            result = service.create_sales_order("BLO-001", [{"item_code": "ITEM-001", "qty": 100}])

        assert result["total"] == 10000.0  # 100 * 100
        assert result["item_count"] == 1
        # ordered_qty 업데이트 검증
        blo_repo.update_by_id.assert_called_once()

    def test_SO_실제_insert_호출(self) -> None:
        """create_sales_order가 SO 문서를 실제로 영속화하는지 검증한다."""
        service, blo_repo, so_repo, _mock_name = _make_service()
        blo_repo.find_by_id.return_value = _sample_blo()

        with patch(
            "oneerp_selling_app.services.blanket_order_service.generate_name",
            return_value="SO-2026-00001",
        ):
            result = service.create_sales_order("BLO-001", [{"item_code": "ITEM-001", "qty": 100}])

        # SO repo insert가 호출되어야 한다
        so_repo.insert.assert_called_once()
        so_doc = so_repo.insert.call_args[0][0]
        assert so_doc["_id"] == "SO-2026-00001"
        assert so_doc["blanket_order_id"] == "BLO-001"
        assert so_doc["total"] == 10000.0
        # 반환값에 so_id 포함
        assert result["so_id"] == "SO-2026-00001"

    def test_잔량초과_에러(self) -> None:
        service, blo_repo, _so, _mock_name = _make_service()
        blo_repo.find_by_id.return_value = _sample_blo()

        with pytest.raises(ValueError, match=r"잔량.*초과"):
            service.create_sales_order(
                "BLO-001", [{"item_code": "ITEM-001", "qty": 900}]
            )  # 잔량 800인데 900 요청

    def test_포괄주문_미존재_에러(self) -> None:
        service, blo_repo, _so, _mock_name = _make_service()
        blo_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.create_sales_order("BLO-999", [])


class Test잔량조회:
    def test_잔량_정확성(self) -> None:
        service, blo_repo, _so, _mock_name = _make_service()
        blo_repo.find_by_id.return_value = _sample_blo()

        result = service.get_remaining_quantities("BLO-001")

        assert len(result) == 2
        assert result[0]["remaining_qty"] == 800.0  # 1000 - 200
        assert result[1]["remaining_qty"] == 500.0  # 500 - 0
