"""품질 검토 서비스(QualityReviewService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_qm_app.quality.services.quality_review_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_qm_app.quality.services.quality_review_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_qm_app.quality.services.quality_review_service import QualityReviewService

        service = QualityReviewService(tenant_id="test-tenant")
    return service, repos["quality_reviews"], repos["quality_actions"], repos["quality_metrics"]


class Test품질검토:
    def test_전항목_합격(self) -> None:
        service, review_repo, action_repo, _metric = _make_service()

        result = service.create_review(
            "PurchaseReceipt",
            "PRCP-001",
            "QC-01",
            [{"description": "외관", "result": "pass"}, {"description": "치수", "result": "pass"}],
        )

        assert result["status"] == "passed"
        assert result["actions_needed"] == 0
        review_repo.insert.assert_called_once()
        action_repo.insert.assert_not_called()

    def test_불합격시_조치생성(self) -> None:
        service, _review, action_repo, _metric = _make_service()

        result = service.create_review(
            "PurchaseReceipt",
            "PRCP-001",
            "QC-01",
            [{"description": "외관", "result": "pass"}, {"description": "치수", "result": "fail"}],
        )

        assert result["status"] == "failed"
        assert result["actions_needed"] == 1
        action_repo.insert.assert_called_once()


class Test품질메트릭:
    def test_목표_달성(self) -> None:
        """값 >= 목표이면 달성 (예: 수율 98% >= 목표 95%)."""
        service, _review, _action, metric_repo = _make_service()

        result = service.record_metric("수율", Decimal("98.0"), Decimal("95.0"), "%")

        assert result["meets_target"] is True
        metric_repo.insert.assert_called_once()

    def test_목표_미달(self) -> None:
        """값 < 목표이면 미달 (예: 수율 90% < 목표 95%)."""
        service, _review, _action, _metric_repo = _make_service()

        result = service.record_metric("수율", Decimal("90.0"), Decimal("95.0"), "%")

        assert result["meets_target"] is False
