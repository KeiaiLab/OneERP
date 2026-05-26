"""ECO 서비스(ECOService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_plm_app.services.eco_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """서비스와 mock 저장소를 생성한다."""
    with patch("oneerp_plm_app.services.eco_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_plm_app.services.eco_service import ECOService

        service = ECOService(tenant_id="test-tenant")
    return service, repos


class TestECO제출:
    """ECO 제출 테스트."""

    def test_정상_제출(self) -> None:
        """draft 상태에서 ECO를 제출할 수 있다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "draft",
            "proposed_changes": [{"change_target_type": "bom"}],
        }

        result = service.submit_eco("ECO-001")

        assert result["status"] == "submitted"
        repos["eng_change_orders"].update_by_id.assert_called_once()

    def test_제안변경_없이_제출_실패(self) -> None:
        """제안 변경이 없으면 제출할 수 없다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "draft",
            "proposed_changes": [],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.submit_eco("ECO-001")
        assert "제안 변경" in (exc_info.value.detail or "")

    def test_이미_제출된_ECO_재제출_실패(self) -> None:
        """submitted 상태에서 재제출이 불가하다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "submitted",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.submit_eco("ECO-001")
        assert "제출할 수 없습니다" in (exc_info.value.detail or "")

    def test_ECO_미존재(self) -> None:
        """존재하지 않는 ECO 제출 시도가 실패한다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.submit_eco("ECO-999")
        assert exc_info.value.status_code == 404


class TestECO검토자배정:
    """ECO 검토자 배정 테스트."""

    def test_정상_검토자_배정(self) -> None:
        """검토자를 배정하면 in_review 상태로 전환된다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "submitted",
        }

        result = service.assign_reviewers(
            "ECO-001",
            [{"reviewer_id": "USR-001", "review_role": "production"}],
        )

        assert result["status"] == "in_review"
        assert result["reviewer_count"] == 1

    def test_빈_검토자_배정_실패(self) -> None:
        """빈 검토자 목록으로 배정하면 실패한다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "submitted",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.assign_reviewers("ECO-001", [])
        assert "1명 이상" in (exc_info.value.detail or "")


class TestECO검토:
    """ECO 검토 제출 테스트."""

    def test_정상_검토_제출(self) -> None:
        """배정된 검토자가 검토를 제출할 수 있다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "pending"},
            ],
        }

        result = service.submit_review("ECO-001", "USR-001", "approved", "승인합니다")

        assert result["review_status"] == "approved"

    def test_미배정_검토자_검토_실패(self) -> None:
        """배정되지 않은 검토자의 검토가 실패한다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "pending"},
            ],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.submit_review("ECO-001", "USR-999", "approved")
        assert "배정된 검토자" in (exc_info.value.detail or "")


class TestECO승인:
    """ECO 승인 테스트."""

    def test_정상_승인_ECN_자동생성(self) -> None:
        """모든 검토 완료 후 승인 시 ECN이 자동 생성된다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "is_emergency": False,
            "title": "테스트 ECO",
            "description": "테스트",
            "affected_products": ["PRD-001"],
            "target_effective_date": "2026-05-01",
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "approved"},
                {"reviewer_id": "USR-002", "review_status": "approved"},
            ],
        }

        result = service.approve_eco("ECO-001", "USR-LEAD-001")

        assert result["status"] == "approved"
        assert result["ecn_id"] == "ECN-001"
        repos["eng_change_notices"].insert.assert_called_once()

    def test_미완료_검토_있을때_승인_실패(self) -> None:
        """pending 검토가 있으면 승인할 수 없다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "is_emergency": False,
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "approved"},
                {"reviewer_id": "USR-002", "review_status": "pending"},
            ],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.approve_eco("ECO-001", "USR-LEAD-001")
        assert "미완료 검토" in (exc_info.value.detail or "")

    def test_거부된_검토_있을때_승인_실패(self) -> None:
        """rejected 검토가 있으면 승인할 수 없다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "is_emergency": False,
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "approved"},
                {"reviewer_id": "USR-002", "review_status": "rejected"},
            ],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.approve_eco("ECO-001", "USR-LEAD-001")
        assert "거부된 검토" in (exc_info.value.detail or "")

    def test_긴급ECO_1명승인시_성공(self) -> None:
        """긴급 ECO는 1명 이상 승인이면 승인 가능하다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "status": "in_review",
            "is_emergency": True,
            "title": "긴급 ECO",
            "description": "긴급",
            "affected_products": ["PRD-001"],
            "reviewers": [
                {"reviewer_id": "USR-001", "review_status": "approved"},
                {"reviewer_id": "USR-002", "review_status": "pending"},
            ],
        }

        result = service.approve_eco("ECO-001", "USR-LEAD-001")
        assert result["status"] == "approved"


class TestECO영향도분석:
    """ECO 영향도 분석 테스트."""

    def test_정상_영향도_분석(self) -> None:
        """영향도 분석이 올바르게 집계된다."""
        service, repos = _make_service()
        repos["eng_change_orders"].find_by_id.return_value = {
            "_id": "ECO-001",
            "affected_products": ["PRD-001"],
        }
        repos["bom_versions"].find.return_value = [{"_id": "BV-001"}, {"_id": "BV-002"}]
        repos["drawings"].find.return_value = [{"_id": "DWG-001"}]
        repos["certifications"].find.return_value = []

        result = service.analyze_impact("ECO-001")

        assert result["affected_bom_count"] == 2
        assert result["affected_drawing_count"] == 1
        assert result["affected_certification_count"] == 0
        assert result["risk_level"] == "medium"  # 3건 = medium
