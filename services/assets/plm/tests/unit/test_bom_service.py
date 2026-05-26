"""BOM 서비스(BOMService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_plm_app.services.bom_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """서비스와 mock 저장소를 생성한다."""
    with patch("oneerp_plm_app.services.bom_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_plm_app.services.bom_service import BOMService

        service = BOMService(tenant_id="test-tenant")
    return service, repos


class TestBOM릴리즈:
    """BOM 릴리즈 테스트."""

    def test_정상_릴리즈_원가_산출(self) -> None:
        """릴리즈 시 총 원가가 정확히 산출된다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "status": "draft",
            "bom_type": "ebom",
            "product_id": "PRD-001",
            "items": [
                {"item_code": "A", "quantity": 10, "unit_cost": 5},
                {"item_code": "B", "quantity": 3, "unit_cost": 20},
            ],
        }

        result = service.release_bom("BV-001", "USR-001")

        assert result["status"] == "released"
        assert result["total_cost"] == 110.0  # 10*5 + 3*20
        repos["bom_versions"].update_by_id.assert_called_once()
        repos["products"].update_by_id.assert_called_once()

    def test_빈_아이템_릴리즈_실패(self) -> None:
        """구성 품목이 없는 BOM은 릴리즈할 수 없다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "status": "draft",
            "items": [],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.release_bom("BV-001", "USR-001")
        assert "구성 품목이 비어있습니다" in (exc_info.value.detail or "")

    def test_이미_릴리즈된_BOM_재릴리즈_실패(self) -> None:
        """이미 released 상태인 BOM은 릴리즈할 수 없다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "status": "released",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.release_bom("BV-001", "USR-001")
        assert "draft 또는 in_review" in (exc_info.value.detail or "")

    def test_BOM_미존재_릴리즈_실패(self) -> None:
        """존재하지 않는 BOM 릴리즈가 실패한다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.release_bom("BV-999", "USR-001")
        assert exc_info.value.status_code == 404

    def test_MBOM_릴리즈시_active_mbom_갱신(self) -> None:
        """M-BOM 릴리즈 시 제품의 active_mbom_id가 갱신된다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-002",
            "status": "draft",
            "bom_type": "mbom",
            "product_id": "PRD-001",
            "items": [{"item_code": "A", "quantity": 1, "unit_cost": 100}],
        }

        service.release_bom("BV-002", "USR-001")

        repos["products"].update_by_id.assert_called_once_with(
            "PRD-001", {"active_mbom_id": "BV-002"}
        )


class TestBOM비교:
    """BOM 비교(Diff) 테스트."""

    def test_정상_비교_added_removed_modified(self) -> None:
        """BOM 비교 시 added/removed/modified가 정확히 분류된다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.side_effect = [
            {
                "_id": "BV-001",
                "items": [
                    {"item_code": "A", "quantity": 10, "unit_cost": 5},
                    {"item_code": "B", "quantity": 3, "unit_cost": 20},
                ],
            },
            {
                "_id": "BV-002",
                "items": [
                    {"item_code": "B", "quantity": 5, "unit_cost": 20},
                    {"item_code": "C", "quantity": 2, "unit_cost": 30},
                ],
            },
        ]

        result = service.compare_bom("BV-001", "BV-002")

        assert len(result["removed"]) == 1  # A 제거
        assert len(result["added"]) == 1  # C 추가
        assert len(result["modified"]) == 1  # B 수량 변경

    def test_동일_BOM_비교_실패(self) -> None:
        """동일한 BOM을 비교하면 에러가 발생한다."""
        service, _repos = _make_service()

        with pytest.raises(OneERPError) as exc_info:
            service.compare_bom("BV-001", "BV-001")
        assert "동일한 BOM" in (exc_info.value.detail or "")

    def test_비교대상_BOM_미존재(self) -> None:
        """비교 대상 BOM이 존재하지 않으면 에러가 발생한다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.side_effect = [
            {"_id": "BV-001", "items": []},
            None,
        ]

        with pytest.raises(OneERPError) as exc_info:
            service.compare_bom("BV-001", "BV-002")
        assert exc_info.value.status_code == 404


class TestEBOM_MBOM전환:
    """E-BOM → M-BOM 전환 테스트."""

    def test_정상_전환_성공(self) -> None:
        """릴리즈된 E-BOM에서 M-BOM으로 성공적으로 전환한다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "bom_type": "ebom",
            "status": "released",
            "product_id": "PRD-001",
            "base_quantity": 1.0,
            "items": [
                {
                    "item_code": "A",
                    "item_name": "부품A",
                    "quantity": 10,
                    "uom": "EA",
                    "unit_cost": 5,
                },
            ],
        }

        result = service.convert_ebom_to_mbom("BV-001", notes="테스트")

        assert result["mbom_id"] == "BV-001"
        assert result["source_ebom_id"] == "BV-001"
        repos["bom_versions"].insert.assert_called_once()

    def test_MBOM에서_전환_시도_실패(self) -> None:
        """M-BOM은 M-BOM으로 전환할 수 없다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-002",
            "bom_type": "mbom",
            "status": "released",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.convert_ebom_to_mbom("BV-002")
        assert "E-BOM만" in (exc_info.value.detail or "")

    def test_미릴리즈_EBOM_전환_실패(self) -> None:
        """릴리즈되지 않은 E-BOM은 전환할 수 없다."""
        service, repos = _make_service()
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "bom_type": "ebom",
            "status": "draft",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.convert_ebom_to_mbom("BV-001")
        assert "릴리즈된 E-BOM" in (exc_info.value.detail or "")


class TestWhereUsed:
    """Where-Used 분석 테스트."""

    def test_부품_사용처_조회(self) -> None:
        """부품이 사용된 BOM 목록을 반환한다."""
        service, repos = _make_service()
        repos["bom_versions"].find.return_value = [
            {
                "_id": "BV-001",
                "product_id": "PRD-001",
                "bom_type": "ebom",
                "version_label": "1.0",
                "status": "released",
                "items": [{"item_code": "A", "quantity": 10}],
            },
        ]

        result = service.get_where_used("A")

        assert len(result) == 1
        assert result[0]["quantity"] == 10.0
