"""온보딩/오프보딩 서비스(OnboardingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch("oneerp_hr_app.services.onboarding_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_hr_app.services.onboarding_service import OnboardingService

        service = OnboardingService(tenant_id="test-tenant")
    return service, repos["employee_onboardings"], repos["employee_offboardings"]


class Test활동완료:
    def test_활동_완료_처리(self) -> None:
        service, onb_repo, _off = _make_service()
        onb_repo.find_by_id.return_value = {
            "_id": "EOB-001",
            "employee": "EMP-001",
            "activities": [
                {"task": "계정 생성", "status": "pending", "responsible": "IT"},
                {"task": "장비 지급", "status": "pending", "responsible": "총무"},
            ],
        }

        result = service.complete_activity("EOB-001", 0, "onboarding")

        assert result["completed"] == 1
        assert result["total"] == 2
        assert result["progress_pct"] == 50.0
        assert result["all_complete"] is False

    def test_전체_활동_완료(self) -> None:
        service, onb_repo, _off = _make_service()
        onb_repo.find_by_id.return_value = {
            "_id": "EOB-001",
            "activities": [
                {"task": "계정 생성", "status": "completed"},
                {"task": "장비 지급", "status": "pending"},
            ],
        }

        result = service.complete_activity("EOB-001", 1, "onboarding")

        assert result["all_complete"] is True
        assert result["progress_pct"] == 100.0

    def test_잘못된_인덱스_에러(self) -> None:
        service, onb_repo, _off = _make_service()
        onb_repo.find_by_id.return_value = {
            "_id": "EOB-001",
            "activities": [{"task": "T1", "status": "pending"}],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.complete_activity("EOB-001", 5, "onboarding")
        assert exc_info.value.status_code == 422
        assert "범위를 벗어났습니다" in (exc_info.value.detail or "")

    def test_문서_미존재_에러(self) -> None:
        service, onb_repo, _off = _make_service()
        onb_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.complete_activity("EOB-999", 0, "onboarding")
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")


class Test진행상태:
    def test_진행상태_조회(self) -> None:
        service, onb_repo, _off = _make_service()
        onb_repo.find_by_id.return_value = {
            "_id": "EOB-001",
            "employee": "EMP-001",
            "activities": [
                {"task": "계정 생성", "status": "completed", "responsible": "IT"},
                {"task": "장비 지급", "status": "pending", "responsible": "총무"},
            ],
        }

        result = service.get_progress("EOB-001", "onboarding")

        assert result["completed"] == 1
        assert len(result["pending_activities"]) == 1
        assert result["pending_activities"][0]["task"] == "장비 지급"
