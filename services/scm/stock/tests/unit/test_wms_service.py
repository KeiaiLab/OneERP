"""WMS 서비스(WMSService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_stock_app.services.wms_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_stock_app.services.wms_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.wms_service import WMSService

        service = WMSService(tenant_id="test-tenant")
    return service, repos["bin_locations"], repos["putaway_rules"], repos["wave_pickings"]


class Test빈배정:
    def test_규칙기반_배정(self) -> None:
        service, _bin, putaway_repo, _wave = _make_service()
        putaway_repo.find_many.return_value = [{"target_bin": "BIN-A01", "is_active": True}]

        result = service.assign_bin("ITEM-001", "WH-001", 100)

        assert result["bin_id"] == "BIN-A01"
        assert result["method"] == "rule"

    def test_자동_배정(self) -> None:
        service, bin_repo, putaway_repo, _wave = _make_service()
        putaway_repo.find_many.return_value = []
        bin_repo.find_many.return_value = [
            {"_id": "BIN-A01", "available_capacity": 50, "is_active": True},
            {"_id": "BIN-B01", "available_capacity": 200, "is_active": True},
        ]

        result = service.assign_bin("ITEM-001", "WH-001", 100)

        assert result["bin_id"] == "BIN-B01"  # 여유 공간 큰 빈
        assert result["method"] == "auto"

    def test_빈없으면_에러(self) -> None:
        service, bin_repo, putaway_repo, _wave = _make_service()
        putaway_repo.find_many.return_value = []
        bin_repo.find_many.return_value = []

        with pytest.raises(OneERPError) as exc_info:
            service.assign_bin("ITEM-001", "WH-001", 100)
        assert exc_info.value.status_code == 422
        assert exc_info.value.error == "ERR-STK-003"
        assert "사용 가능한 빈이 없습니다" in (exc_info.value.detail or "")


class Test웨이브피킹:
    def test_웨이브_생성(self) -> None:
        service, _bin, _putaway, wave_repo = _make_service()

        result = service.create_wave_picking(["SO-001", "SO-002"], "WH-001")

        assert result["wave_id"] == "WP-001"
        assert result["order_count"] == 2
        wave_repo.insert.assert_called_once()

    def test_주문없으면_에러(self) -> None:
        service, _bin, _putaway, _wave = _make_service()

        with pytest.raises(OneERPError) as exc_info:
            service.create_wave_picking([], "WH-001")
        assert exc_info.value.status_code == 422
        assert exc_info.value.error == "ERR-STK-004"
        assert "1개 이상" in (exc_info.value.detail or "")
