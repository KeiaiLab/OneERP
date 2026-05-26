"""수익 인식 서비스(RevenueRecognitionService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_projects_app.services.revenue_recognition_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch(
        "oneerp_projects_app.services.revenue_recognition_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_projects_app.services.revenue_recognition_service import (
            RevenueRecognitionService,
        )

        service = RevenueRecognitionService(tenant_id="test-tenant")
    return (
        service,
        repos["projects"],
        repos["project_revenue_recognitions"],
        repos["project_billings"],
    )


class Test완료기준수익인식:
    def test_100_완료시_전액_인식(self) -> None:
        service, proj_repo, rec_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 100.0,
        }
        billing_repo.find_many.return_value = [{"total": 50_000_000}]
        rec_repo.find_many.return_value = []

        result = service.recognize_by_completion("PRJ-001", date(2026, 3, 31))

        assert result["recognized_amount"] == Decimal(50000000)
        assert result["completion_percentage"] == Decimal(100)
        rec_repo.insert.assert_called_once()

    def test_미완료시_에러(self) -> None:
        service, proj_repo, _rec, _billing = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 80.0,
        }

        with pytest.raises(OneERPError, match="ERR-PRJ-005"):
            service.recognize_by_completion("PRJ-001", date(2026, 3, 31))

    def test_이미_전액_인식(self) -> None:
        service, proj_repo, rec_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 100.0,
        }
        billing_repo.find_many.return_value = [{"total": 50_000_000}]
        rec_repo.find_many.return_value = [{"recognized_amount": 50_000_000}]

        result = service.recognize_by_completion("PRJ-001", date(2026, 3, 31))

        assert result["recognized_amount"] == Decimal(0)
        rec_repo.insert.assert_not_called()

    def test_프로젝트_미존재(self) -> None:
        service, proj_repo, _rec, _billing = _make_service()
        proj_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.recognize_by_completion("PRJ-999", date(2026, 3, 31))


class Test진행률기준수익인식:
    def test_50_진행률(self) -> None:
        service, proj_repo, rec_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 50.0,
        }
        billing_repo.find_many.return_value = [{"total": 100_000_000}]
        rec_repo.find_many.return_value = []

        result = service.recognize_by_progress("PRJ-001", date(2026, 3, 31))

        # 100M * 50% - 0 = 50M
        assert result["recognized_amount"] == Decimal(50000000)
        assert result["completion_percentage"] == Decimal("50.0")
        rec_repo.insert.assert_called_once()

    def test_기인식_차감(self) -> None:
        service, proj_repo, rec_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 80.0,
        }
        billing_repo.find_many.return_value = [{"total": 100_000_000}]
        rec_repo.find_many.return_value = [{"recognized_amount": 50_000_000}]

        result = service.recognize_by_progress("PRJ-001", date(2026, 3, 31))

        # 100M * 80% - 50M = 30M
        assert result["recognized_amount"] == Decimal(30000000)

    def test_추가_인식_없음(self) -> None:
        service, proj_repo, rec_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {
            "_id": "PRJ-001",
            "percent_complete": 50.0,
        }
        billing_repo.find_many.return_value = [{"total": 100_000_000}]
        rec_repo.find_many.return_value = [{"recognized_amount": 50_000_000}]

        result = service.recognize_by_progress("PRJ-001", date(2026, 3, 31))

        assert result["recognized_amount"] == Decimal(0)
        rec_repo.insert.assert_not_called()
