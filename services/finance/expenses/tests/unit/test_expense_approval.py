"""경비 결재 연동 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_expenses_app.services.expense_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """ExpenseService와 mock Repository를 생성한다."""
    with patch("oneerp_expenses_app.services.expense_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_expenses_app.services.expense_service import ExpenseService

        service = ExpenseService(tenant_id="T001")
    return service, repos["expense_claims"]


class Test결재제출:
    def test_결재_제출_성공_금액별_결재선(self) -> None:
        """금액에 따라 결재 템플릿이 자동으로 선택된다 (50만원 → 부장)."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = {
            "_id": "EC-0001",
            "employee": "EMP-001",
            "total_amount": 500_000,  # 50만원: 100만 미만 → 부장 결재
            "status": "draft",
        }

        with patch("oneerp_expenses_app.services.expense_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "AR-0001"}
            mock_response.raise_for_status = MagicMock()
            mock_httpx.post.return_value = mock_response

            result = service.submit_for_approval("EC-0001")

        assert result["approval_request_id"] == "AR-0001"
        assert result["approver_level"] == "부장"
        claim_repo.update_by_id.assert_called_once()

    def test_결재_제출_10만_미만_팀장(self) -> None:
        """10만원 미만이면 팀장 결재."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = {
            "_id": "EC-0003",
            "employee": "EMP-001",
            "total_amount": 50_000,  # 5만원 → 팀장
            "status": "draft",
        }

        with patch("oneerp_expenses_app.services.expense_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "AR-0003"}
            mock_response.raise_for_status = MagicMock()
            mock_httpx.post.return_value = mock_response

            result = service.submit_for_approval("EC-0003")

        assert result["approver_level"] == "팀장"

    def test_결재_제출_100만_이상_임원(self) -> None:
        """100만원 이상이면 임원 결재."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = {
            "_id": "EC-0004",
            "employee": "EMP-001",
            "total_amount": 1_500_000,  # 150만원 → 임원
            "status": "draft",
        }

        with patch("oneerp_expenses_app.services.expense_service.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "AR-0004"}
            mock_response.raise_for_status = MagicMock()
            mock_httpx.post.return_value = mock_response

            result = service.submit_for_approval("EC-0004")

        assert result["approver_level"] == "임원"

    def test_결재_제출_미존재_경비_에러(self) -> None:
        """존재하지 않는 경비청구 ID면 OneERPError(404)."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.submit_for_approval("EC-9999")


class Test승인처리:
    def test_승인후_이벤트_발행(self) -> None:
        """process_approved_expense 호출 시 status가 approved로 변경된다."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = {
            "_id": "EC-0002",
            "employee": "EMP-002",
            "total_amount": 80_000,
            "status": "pending_approval",
        }

        service.process_approved_expense("EC-0002")

        claim_repo.update_by_id.assert_called_once_with(
            "EC-0002",
            {"status": "approved"},
        )

    def test_승인_미존재_경비_에러(self) -> None:
        """존재하지 않는 경비청구 ID면 OneERPError(404)."""
        service, claim_repo = _make_service()
        claim_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.process_approved_expense("EC-9999")
