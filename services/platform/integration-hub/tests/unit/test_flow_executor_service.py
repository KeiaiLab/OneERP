"""FlowExecutorService 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_integration_hub_app.services.flow_executor_service import FlowExecutorService


@pytest.fixture
def mock_repos():
    """Mock Repository 인스턴스를 반환한다."""
    with patch(
        "oneerp_integration_hub_app.services.flow_executor_service.Repository"
    ) as mock_repo_cls:
        flow_repo = MagicMock()
        connector_repo = MagicMock()
        mapping_repo = MagicMock()
        log_repo = MagicMock()

        mock_repo_cls.side_effect = [flow_repo, connector_repo, mapping_repo, log_repo]

        yield {
            "flow_repo": flow_repo,
            "connector_repo": connector_repo,
            "mapping_repo": mapping_repo,
            "log_repo": log_repo,
        }


@pytest.fixture
def service(mock_repos):
    """FlowExecutorService 인스턴스를 반환한다."""
    return FlowExecutorService(tenant_id="test-tenant")


class TestExecuteFlow:
    """플로우 실행 테스트."""

    def test_플로우_실행_성공(self, service, mock_repos) -> None:
        """활성 플로우 실행 시 success를 반환한다."""
        mock_repos["flow_repo"].find_by_id.return_value = {
            "_id": "IFLOW-00001",
            "flow_name": "테스트 플로우",
            "is_active": True,
            "source_connector_id": "CONN-001",
            "mapping_id": "DMAP-001",
            "steps": [
                {"step_type": "extract", "config": {"batch_size": 50}},
                {"step_type": "load", "config": {"batch_size": 50}},
            ],
        }
        mock_repos["connector_repo"].find_by_id.return_value = {"_id": "CONN-001"}
        mock_repos["mapping_repo"].find_by_id.return_value = {"_id": "DMAP-001"}

        result = service.execute_flow("IFLOW-00001")

        assert result["status"] == "success"
        assert result["records_processed"] == 100  # 50 * 2 단계
        mock_repos["log_repo"].insert.assert_called_once()

    def test_미존재_플로우_에러(self, service, mock_repos) -> None:
        """존재하지 않는 플로우 ID이면 ValueError가 발생한다."""
        mock_repos["flow_repo"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="통합 플로우를 찾을 수 없습니다"):
            service.execute_flow("IFLOW-99999")

    def test_비활성_플로우_에러(self, service, mock_repos) -> None:
        """비활성 플로우이면 ValueError가 발생한다."""
        mock_repos["flow_repo"].find_by_id.return_value = {
            "_id": "IFLOW-00002",
            "is_active": False,
        }

        with pytest.raises(ValueError, match="비활성 플로우"):
            service.execute_flow("IFLOW-00002")


class TestTransformData:
    """데이터 변환 테스트."""

    def test_직접매핑_변환(self, service, mock_repos) -> None:
        """direct 변환은 값을 그대로 복사한다."""
        mock_repos["mapping_repo"].find_by_id.return_value = {
            "_id": "DMAP-001",
            "field_mappings": [
                {"source_field": "name", "target_field": "company_name", "transform": "direct"},
                {"source_field": "code", "target_field": "company_code", "transform": "uppercase"},
            ],
        }

        result = service.transform_data(
            "DMAP-001",
            [{"name": "테스트회사", "code": "abc"}],
        )

        assert result["success"] == 1
        assert result["failed"] == 0
        assert result["transformed_data"][0]["company_name"] == "테스트회사"
        assert result["transformed_data"][0]["company_code"] == "ABC"

    def test_매핑_미존재_에러(self, service, mock_repos) -> None:
        """매핑 설정이 없으면 ValueError가 발생한다."""
        mock_repos["mapping_repo"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="데이터 매핑을 찾을 수 없습니다"):
            service.transform_data("DMAP-99999", [])

    def test_빈_데이터_변환(self, service, mock_repos) -> None:
        """빈 소스 데이터에 대해 빈 결과를 반환한다."""
        mock_repos["mapping_repo"].find_by_id.return_value = {
            "_id": "DMAP-002",
            "field_mappings": [],
        }

        result = service.transform_data("DMAP-002", [])

        assert result["total"] == 0
        assert result["success"] == 0
