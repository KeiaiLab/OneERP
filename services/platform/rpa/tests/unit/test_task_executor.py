"""TaskExecutor 단위 테스트."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from oneerp_rpa_app.services.appium_manager import AppiumManager
from oneerp_rpa_app.services.task_executor import TaskExecutor


@pytest.fixture
def mock_appium_manager() -> AppiumManager:
    """모든 메서드가 AsyncMock인 AppiumManager를 반환한다."""
    manager = MagicMock(spec=AppiumManager)
    manager.create_android_session = AsyncMock(return_value="test-session-id")
    manager.close_session = AsyncMock()
    manager.find_and_click = AsyncMock(return_value=True)
    manager.find_and_input = AsyncMock(return_value=True)
    manager.wait_for_element = AsyncMock(return_value=True)
    manager.take_screenshot = AsyncMock(return_value=b"fake-png-data")
    return manager


@pytest.fixture
def mock_repos():
    """Mock Repository 인스턴스를 반환한다."""
    with (
        patch("oneerp_rpa_app.services.task_executor.Repository") as mock_repo_cls,
        patch("oneerp_rpa_app.services.task_executor.generate_name", return_value="RPAR-00001"),
    ):
        task_repo = MagicMock()
        result_repo = MagicMock()

        # Repository() 호출 시 순서대로 반환
        mock_repo_cls.side_effect = [task_repo, result_repo]

        yield {"task_repo": task_repo, "result_repo": result_repo}


@pytest.fixture
def executor(mock_repos, mock_appium_manager):
    """TaskExecutor 인스턴스를 반환한다. AppiumManager는 mock으로 대체."""
    with patch(
        "oneerp_rpa_app.services.task_executor.AppiumManager", return_value=mock_appium_manager
    ):
        return TaskExecutor(tenant_id="test-tenant")


class TestExecuteTask성공:
    """작업 실행 성공 시나리오."""

    def test_hometax_issue_실행_성공(self, executor, mock_repos, mock_appium_manager) -> None:
        """hometax_issue 작업이 정상 실행되면 completed 상태가 된다."""
        task_doc = {
            "_id": "RPAT-00001",
            "task_type": "hometax_issue",
            "input_data": {
                "cert_password": "test1234",
                "invoice_data": {"supplier": {}, "buyer": {}},
            },
            "device_id": "emulator-5554",
            "retry_count": 0,
            "max_retries": 3,
        }
        mock_repos["task_repo"].find_by_id.return_value = task_doc

        result = asyncio.run(executor.execute_task("RPAT-00001"))

        assert result["status"] == "completed"
        assert "result" in result
        # running 상태로 변경 호출 확인
        first_update = mock_repos["task_repo"].update_by_id.call_args_list[0]
        assert first_update[0][1]["status"] == "running"
        # completed 상태로 변경 호출 확인
        second_update = mock_repos["task_repo"].update_by_id.call_args_list[1]
        assert second_update[0][1]["status"] == "completed"
        # RPAResult 저장 확인
        mock_repos["result_repo"].insert.assert_called_once()

    def test_banking_balance_실행_성공(self, executor, mock_repos, mock_appium_manager) -> None:
        """banking_balance 작업이 정상 실행된다."""
        task_doc = {
            "_id": "RPAT-00002",
            "task_type": "banking_balance",
            "input_data": {
                "app_package": "com.kbstar.banking",
                "account": "123-456-789",
            },
            "device_id": "emulator-5554",
            "retry_count": 0,
            "max_retries": 3,
        }
        mock_repos["task_repo"].find_by_id.return_value = task_doc

        result = asyncio.run(executor.execute_task("RPAT-00002"))

        assert result["status"] == "completed"
        mock_appium_manager.create_android_session.assert_called_once()

    def test_insurance_status_실행_성공(self, executor, mock_repos, mock_appium_manager) -> None:
        """insurance_status 작업이 정상 실행된다."""
        task_doc = {
            "_id": "RPAT-00003",
            "task_type": "insurance_status",
            "input_data": {
                "app_package": "com.nhis.insurance",
                "policy_number": "POL-001",
            },
            "device_id": "emulator-5554",
            "retry_count": 0,
            "max_retries": 3,
        }
        mock_repos["task_repo"].find_by_id.return_value = task_doc

        result = asyncio.run(executor.execute_task("RPAT-00003"))

        assert result["status"] == "completed"


class TestExecuteTask실패:
    """작업 실행 실패 시나리오."""

    def test_실패_시_재시도_pending(self, executor, mock_repos, mock_appium_manager) -> None:
        """실행 실패 시 retry_count < max_retries이면 pending으로 복귀한다."""
        task_doc = {
            "_id": "RPAT-00010",
            "task_type": "hometax_issue",
            "input_data": {"cert_password": "test"},
            "device_id": "emulator-5554",
            "retry_count": 0,
            "max_retries": 3,
        }
        mock_repos["task_repo"].find_by_id.return_value = task_doc

        # Runner 시작 시 예외 발생
        mock_appium_manager.create_android_session = AsyncMock(
            side_effect=RuntimeError("Appium 연결 실패"),
        )

        result = asyncio.run(executor.execute_task("RPAT-00010"))

        assert result["status"] == "pending"
        assert result["retry_count"] == 1
        assert "Appium 연결 실패" in result["error"]

    def test_실패_최대초과_failed(self, executor, mock_repos, mock_appium_manager) -> None:
        """retry_count >= max_retries이면 failed로 확정된다."""
        task_doc = {
            "_id": "RPAT-00011",
            "task_type": "hometax_query",
            "input_data": {"cert_password": "test", "period": "202601"},
            "device_id": "emulator-5554",
            "retry_count": 2,
            "max_retries": 3,
        }
        mock_repos["task_repo"].find_by_id.return_value = task_doc

        mock_appium_manager.create_android_session = AsyncMock(
            side_effect=RuntimeError("세션 생성 실패"),
        )

        result = asyncio.run(executor.execute_task("RPAT-00011"))

        assert result["status"] == "failed"
        assert result["retry_count"] == 3
        # completed_at 설정 확인
        last_update = mock_repos["task_repo"].update_by_id.call_args_list[-1]
        assert last_update[0][1]["completed_at"] is not None

    def test_미존재_작업_에러(self, executor, mock_repos) -> None:
        """존재하지 않는 task_id로 실행하면 ValueError가 발생한다."""
        mock_repos["task_repo"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="작업을 찾을 수 없습니다"):
            asyncio.run(executor.execute_task("RPAT-99999"))

    def test_미지원_작업유형_에러(self, executor, mock_repos) -> None:
        """지원하지 않는 task_type이면 ValueError가 발생한다."""
        mock_repos["task_repo"].find_by_id.return_value = {
            "_id": "RPAT-00020",
            "task_type": "unknown_type",
            "input_data": {},
        }

        with pytest.raises(ValueError, match="지원하지 않는 작업 유형"):
            asyncio.run(executor.execute_task("RPAT-00020"))
