"""피킹/포장 서비스(PickPackService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_stock_app.services.pick_pack_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_stock_app.services.pick_pack_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.pick_pack_service import PickPackService

        service = PickPackService(tenant_id="test-tenant")
    return service, repos["pick_lists"], repos["packing_slips"], repos["sales_orders"]


class Test피킹리스트:
    def test_SO에서_피킹리스트_생성(self) -> None:
        service, pick_repo, _pack, so_repo = _make_service()
        so_repo.find_by_id.return_value = {
            "_id": "SO-001",
            "items": [
                {"item_code": "ITEM-001", "qty": 10, "warehouse": "WH-001"},
                {"item_code": "ITEM-002", "qty": 5, "warehouse": "WH-001"},
            ],
        }

        result = service.create_pick_list("SO-001")

        assert result["pick_list_id"] == "PL-001"
        assert result["item_count"] == 2
        pick_repo.insert.assert_called_once()

    def test_SO_미존재_에러(self) -> None:
        service, _pick, _pack, so_repo = _make_service()
        so_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.create_pick_list("SO-999")
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")


class Test포장전표:
    def test_피킹완료후_포장생성(self) -> None:
        service, pick_repo, pack_repo, _so = _make_service()
        pick_repo.find_by_id.return_value = {
            "_id": "PL-001",
            "items": [
                {"item_code": "ITEM-001", "qty": 10, "picked_qty": 10},
            ],
        }

        result = service.create_packing_slip("PL-001")

        assert result["packing_slip_id"] == "PS-001"
        assert result["item_count"] == 1
        pack_repo.insert.assert_called_once()

    def test_미피킹시_에러(self) -> None:
        service, pick_repo, _pack, _so = _make_service()
        pick_repo.find_by_id.return_value = {
            "_id": "PL-001",
            "items": [
                {"item_code": "ITEM-001", "qty": 10, "picked_qty": 5},
            ],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.create_packing_slip("PL-001")
        assert exc_info.value.status_code == 422
        assert exc_info.value.error == "ERR-STK-002"
        assert "미피킹 아이템" in (exc_info.value.detail or "")

    def test_PL_미존재_에러(self) -> None:
        service, pick_repo, _pack, _so = _make_service()
        pick_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.create_packing_slip("PL-999")
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")
