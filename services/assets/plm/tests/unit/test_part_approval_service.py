"""부품 승인 서비스(PartApprovalService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """서비스와 mock 저장소를 생성한다."""
    with patch("oneerp_plm_app.services.part_approval_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_plm_app.services.part_approval_service import PartApprovalService

        service = PartApprovalService(tenant_id="test-tenant")
    return service, repos


class Test기술검토:
    """기술 검토 테스트."""

    def test_정상_기술검토_pass(self) -> None:
        """기술 검토를 pass로 제출할 수 있다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "requested",
        }

        result = service.submit_technical_review(
            "PAR-001",
            reviewer_id="USR-ENG-001",
            result="pass",
            spec_compliance=True,
            form_fit_function=True,
            reliability_assessment="MTBF 100,000시간",
        )

        assert result["review_type"] == "technical"
        assert result["result"] == "pass"
        repos["part_approvals"].update_by_id.assert_called_once()

    def test_미존재_승인_기술검토_실패(self) -> None:
        """존재하지 않는 승인에 대한 검토가 실패한다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.submit_technical_review("PAR-999", "USR-001", "pass")
        assert exc_info.value.status_code == 404


class Test품질검토:
    """품질 검토 테스트."""

    def test_정상_품질검토_pass(self) -> None:
        """품질 검토를 pass로 제출할 수 있다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "technical_review",
        }

        result = service.submit_quality_review(
            "PAR-001",
            reviewer_id="USR-QA-001",
            result="pass",
            incoming_inspection_plan=True,
            supplier_quality_rating="A",
            rohs_compliance=True,
        )

        assert result["review_type"] == "quality"
        assert result["result"] == "pass"


class Test비용검토:
    """비용 검토 테스트."""

    def test_정상_비용검토_pass(self) -> None:
        """비용 검토를 pass로 제출할 수 있다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "quality_review",
        }

        result = service.submit_cost_review(
            "PAR-001",
            reviewer_id="USR-BUY-001",
            result="pass",
            unit_price=3500.0,
            moq=100,
            lead_time_days=14,
        )

        assert result["review_type"] == "cost"
        assert result["result"] == "pass"


class Test최종승인:
    """최종 승인 테스트."""

    def test_3중검토_완료후_승인_성공(self) -> None:
        """3중 검토가 모두 pass인 경우 최종 승인이 성공한다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "cost_review",
            "technical_review": {"result": "pass"},
            "quality_review": {"result": "pass"},
            "cost_review": {"result": "pass"},
        }

        result = service.approve("PAR-001", "USR-LEAD-001")

        assert result["status"] == "approved"
        repos["part_approvals"].update_by_id.assert_called_once()

    def test_기술검토_미완료시_승인_실패(self) -> None:
        """기술 검토가 미완료인 경우 승인할 수 없다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "quality_review",
            "technical_review": None,
            "quality_review": {"result": "pass"},
            "cost_review": {"result": "pass"},
        }

        with pytest.raises(OneERPError) as exc_info:
            service.approve("PAR-001", "USR-LEAD-001")
        assert "3중 검토" in (exc_info.value.detail or "")

    def test_품질검토_fail시_승인_실패(self) -> None:
        """품질 검토가 fail인 경우 승인할 수 없다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "cost_review",
            "technical_review": {"result": "pass"},
            "quality_review": {"result": "fail"},
            "cost_review": {"result": "pass"},
        }

        with pytest.raises(OneERPError) as exc_info:
            service.approve("PAR-001", "USR-LEAD-001")
        assert "3중 검토" in (exc_info.value.detail or "")

    def test_조건부_승인(self) -> None:
        """조건부 승인이 conditional 상태로 처리된다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = {
            "_id": "PAR-001",
            "status": "cost_review",
            "technical_review": {"result": "pass"},
            "quality_review": {"result": "conditional"},
            "cost_review": {"result": "pass"},
        }

        result = service.approve("PAR-001", "USR-LEAD-001", conditions="6개월 후 재검토")

        assert result["status"] == "conditional"

    def test_미존재_승인_최종승인_실패(self) -> None:
        """존재하지 않는 승인에 대한 최종 승인이 실패한다."""
        service, repos = _make_service()
        repos["part_approvals"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.approve("PAR-999", "USR-001")
        assert exc_info.value.status_code == 404
