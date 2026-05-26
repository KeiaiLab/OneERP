"""성과 평가 서비스(PerformanceAppraisalService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """서비스와 appraisals 레포 mock 을 생성한다."""
    with patch("oneerp_hr_app.services.performance_appraisal_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name not in repos:
                repos[collection_name] = MagicMock()
            return repos[collection_name]

        mock_repo_cls.side_effect = _factory
        from oneerp_hr_app.services.performance_appraisal_service import (
            PerformanceAppraisalService,
        )

        service = PerformanceAppraisalService(tenant_id="test-tenant")
    return service, repos.setdefault("appraisals", MagicMock())


class Test평가생성:
    """BR-HR-028: 평가 사이클 내 중복 평가 방지."""

    def test_신규_평가_생성_성공(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_many.return_value = []

        result = service.create_appraisal(
            employee_id="EMP-001",
            appraisal_cycle_id="APRC-2026",
            reviewer_id="EMP-999",
        )

        assert result["status"] == "draft"
        appraisal_repo.insert.assert_called_once()

    def test_중복_평가_생성시_422(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_many.return_value = [{"_id": "APR-001", "employee_id": "EMP-001"}]

        with pytest.raises(OneERPError) as exc_info:
            service.create_appraisal(
                employee_id="EMP-001",
                appraisal_cycle_id="APRC-2026",
            )
        assert exc_info.value.status_code == 422
        assert "이미 존재" in (exc_info.value.detail or "")


class Test상태전이:
    """BR-HR-025: 평가 상태 머신 전이 규칙."""

    def test_draft_to_self_review_정상(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-001",
            "status": "draft",
        }

        result = service.transition_status("APR-001", "self_review")

        assert result["from_status"] == "draft"
        assert result["to_status"] == "self_review"
        appraisal_repo.update_by_id.assert_called_once()

    def test_단계_건너뛰기_실패(self) -> None:
        """draft → manager_review (self_review 건너뛰기)는 불가."""
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-002",
            "status": "draft",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_status("APR-002", "manager_review")
        assert exc_info.value.status_code == 422

    def test_역방향_전이_실패(self) -> None:
        """manager_review → self_review 역방향 전이 불가."""
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-003",
            "status": "manager_review",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_status("APR-003", "self_review")
        assert exc_info.value.status_code == 422

    def test_completed_에서_전이_불가(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-004",
            "status": "completed",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.transition_status("APR-004", "calibrated")
        assert exc_info.value.status_code == 422

    def test_평가_없음_404(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.transition_status("APR-NONE", "self_review")
        assert exc_info.value.status_code == 404


class Test가중점수계산:
    """BR-HR-027: 목표 가중 평균 점수."""

    def test_가중평균_정상(self) -> None:
        service, _repo = _make_service()
        goals = [
            {"goal_score": 5, "weight": 0.5},
            {"goal_score": 3, "weight": 0.5},
        ]
        score = service.calculate_weighted_score(goals)
        assert score == Decimal("4.00")

    def test_가중치_불균등(self) -> None:
        service, _repo = _make_service()
        goals = [
            {"goal_score": 4, "weight": 0.8},
            {"goal_score": 2, "weight": 0.2},
        ]
        # (4*0.8 + 2*0.2) / 1.0 = 3.6
        score = service.calculate_weighted_score(goals)
        assert score == Decimal("3.60")

    def test_빈_목표_422(self) -> None:
        service, _repo = _make_service()
        with pytest.raises(OneERPError) as exc_info:
            service.calculate_weighted_score([])
        assert exc_info.value.status_code == 422

    def test_점수_범위_초과_422(self) -> None:
        service, _repo = _make_service()
        with pytest.raises(OneERPError) as exc_info:
            service.calculate_weighted_score(
                [{"goal_score": 6, "weight": 1}],
            )
        assert exc_info.value.status_code == 422

    def test_가중치_합계_0_422(self) -> None:
        service, _repo = _make_service()
        with pytest.raises(OneERPError) as exc_info:
            service.calculate_weighted_score(
                [{"goal_score": 3, "weight": 0}],
            )
        assert exc_info.value.status_code == 422


class Test등급환산:
    """BR-HR-026: 점수 → 등급."""

    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (Decimal("5.0"), "S"),
            (Decimal("4.5"), "S"),
            (Decimal("4.4"), "A"),
            (Decimal("4.0"), "A"),
            (Decimal("3.9"), "B"),
            (Decimal("3.0"), "B"),
            (Decimal("2.9"), "C"),
            (Decimal("2.0"), "C"),
            (Decimal("1.9"), "D"),
            (Decimal("0.0"), "D"),
        ],
    )
    def test_점수별_등급(self, score: Decimal, expected: str) -> None:
        service, _repo = _make_service()
        assert service.score_to_grade(score) == expected


class Test점수확정:
    def test_manager_review_상태에서_점수_확정(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-010",
            "status": "manager_review",
        }
        goals = [
            {"goal_score": 5, "weight": 0.5},
            {"goal_score": 4, "weight": 0.5},
        ]

        result = service.finalize_score("APR-010", goals)

        assert result["score"] == "4.50"
        assert result["grade"] == "S"
        appraisal_repo.update_by_id.assert_called_once()

    def test_draft_상태에서_점수_확정_실패(self) -> None:
        service, appraisal_repo = _make_service()
        appraisal_repo.find_by_id.return_value = {
            "_id": "APR-011",
            "status": "draft",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.finalize_score(
                "APR-011",
                [{"goal_score": 4, "weight": 1}],
            )
        assert exc_info.value.status_code == 422
