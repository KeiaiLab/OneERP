"""제품 수명주기 서비스(ProductLifecycleService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """서비스와 mock 저장소를 생성한다."""
    with patch("oneerp_plm_app.services.product_lifecycle_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_plm_app.services.product_lifecycle_service import ProductLifecycleService

        service = ProductLifecycleService(tenant_id="test-tenant")
    return service, repos


class Test제품수명주기:
    """제품 수명주기 전이 테스트."""

    def test_concept에서_design으로_전이_성공(self) -> None:
        """concept → design 전이가 성공한다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "concept",
        }

        result = service.transition_lifecycle("PRD-001", "design", "설계 시작")

        assert result["new_status"] == "design"
        assert result["previous_status"] == "concept"
        repos["products"].update_by_id.assert_called_once()

    def test_concept에서_production으로_직접_전이_실패(self) -> None:
        """concept → production 직접 전이가 차단된다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "concept",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "production")
        assert "허용되지 않는 상태 전이" in (exc_info.value.detail or "")

    def test_design에서_prototype_전이_ebom_필수(self) -> None:
        """design → prototype 전이 시 릴리즈된 E-BOM이 필요하다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "design",
            "active_ebom_id": None,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "prototype")
        assert "E-BOM" in (exc_info.value.detail or "")

    def test_design에서_prototype_전이_ebom_릴리즈_확인(self) -> None:
        """design → prototype 전이 시 E-BOM이 released 상태여야 한다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "design",
            "active_ebom_id": "BV-001",
        }
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "status": "draft",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "prototype")
        assert "릴리즈 상태가 아닙니다" in (exc_info.value.detail or "")

    def test_design에서_prototype_전이_ebom_릴리즈_성공(self) -> None:
        """design → prototype 전이가 E-BOM 릴리즈 상태에서 성공한다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "design",
            "active_ebom_id": "BV-001",
        }
        repos["bom_versions"].find_by_id.return_value = {
            "_id": "BV-001",
            "status": "released",
        }

        result = service.transition_lifecycle("PRD-001", "prototype")
        assert result["new_status"] == "prototype"

    def test_prototype에서_pre_production_전이_mbom_필수(self) -> None:
        """prototype → pre_production 전이 시 M-BOM이 필요하다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "prototype",
            "active_mbom_id": None,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "pre_production")
        assert "M-BOM" in (exc_info.value.detail or "")

    def test_end_of_life에서_전이_불가(self) -> None:
        """end_of_life 상태에서 어떤 전이도 불가능하다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "end_of_life",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "production")
        assert "허용되지 않는 상태 전이" in (exc_info.value.detail or "")

    def test_제품_미존재(self) -> None:
        """존재하지 않는 제품에 대한 전이 시도가 실패한다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-999", "design")
        assert exc_info.value.status_code == 404

    def test_phase_out에서_production_복귀_성공(self) -> None:
        """phase_out → production 복귀가 가능하다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "phase_out",
        }

        result = service.transition_lifecycle("PRD-001", "production")
        assert result["new_status"] == "production"

    def test_유효하지_않은_상태값(self) -> None:
        """유효하지 않은 상태값에 대해 에러를 반환한다."""
        service, repos = _make_service()
        repos["products"].find_by_id.return_value = {
            "_id": "PRD-001",
            "lifecycle_status": "concept",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_lifecycle("PRD-001", "invalid_status")
        assert "유효하지 않은 상태" in (exc_info.value.detail or "")
