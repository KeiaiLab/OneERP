"""아이템 변형 서비스(ItemVariantService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_stock_app.services.item_variant_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_stock_app.services.item_variant_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.item_variant_service import ItemVariantService

        service = ItemVariantService(tenant_id="test-tenant")
    return service, repos["item_variants"], repos["items"]


class Test변형생성:
    def test_2속성_조합생성(self) -> None:
        """2개 속성 조합으로 변형을 생성한다."""
        service, variant_repo, item_repo = _make_service()
        item_repo.find_by_id.return_value = {"_id": "TSHIRT", "item_name": "티셔츠"}

        result = service.generate_variants(
            "TSHIRT",
            {"색상": ["빨강", "파랑"], "사이즈": ["S", "M"]},
        )

        assert result["variant_count"] == 4  # 2 x 2
        assert variant_repo.insert.call_count == 4

    def test_단일속성(self) -> None:
        service, _variant_repo, item_repo = _make_service()
        item_repo.find_by_id.return_value = {"_id": "PEN", "item_name": "볼펜"}

        result = service.generate_variants("PEN", {"색상": ["빨강", "파랑", "검정"]})

        assert result["variant_count"] == 3

    def test_템플릿_미존재_에러(self) -> None:
        service, _variant, item_repo = _make_service()
        item_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.generate_variants("UNKNOWN", {"색상": ["빨강"]})
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_속성_미지정_에러(self) -> None:
        service, _variant, item_repo = _make_service()
        item_repo.find_by_id.return_value = {"_id": "ITEM", "item_name": "아이템"}

        with pytest.raises(OneERPError) as exc_info:
            service.generate_variants("ITEM", {})
        assert exc_info.value.status_code == 422
        assert exc_info.value.error == "ERR-STK-005"
        assert "속성을 1개 이상" in (exc_info.value.detail or "")
