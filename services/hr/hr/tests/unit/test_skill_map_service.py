"""역량 평가 서비스(SkillMapService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch("oneerp_hr_app.services.skill_map_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_hr_app.services.skill_map_service import SkillMapService

        service = SkillMapService(tenant_id="test-tenant")
    return service, repos["employee_skill_maps"], repos["employees"]


class Test역량평가:
    def test_정상_평가(self) -> None:
        service, skill_repo, _emp = _make_service()
        skill_repo.find_many.return_value = []

        result = service.evaluate_skills("EMP-001", {"Python": 5, "SQL": 4, "리더십": 3})

        assert result["skill_count"] == 3
        assert result["average_score"] == 4.0
        skill_repo.insert.assert_called_once()

    def test_기존_평가_업데이트(self) -> None:
        service, skill_repo, _emp = _make_service()
        skill_repo.find_many.return_value = [{"_id": "ESM-001", "skills": {"Python": 3}}]

        result = service.evaluate_skills("EMP-001", {"Python": 5})

        assert result["average_score"] == 5.0
        skill_repo.update_by_id.assert_called_once()

    def test_빈역량_에러(self) -> None:
        service, _skill, _emp = _make_service()

        with pytest.raises(OneERPError) as exc_info:
            service.evaluate_skills("EMP-001", {})
        assert exc_info.value.status_code == 422
        assert "1개 이상" in (exc_info.value.detail or "")

    def test_범위초과_에러(self) -> None:
        service, _skill, _emp = _make_service()

        with pytest.raises(OneERPError) as exc_info:
            service.evaluate_skills("EMP-001", {"Python": 6})
        assert exc_info.value.status_code == 422
        assert "1~5 범위" in (exc_info.value.detail or "")


class Test부서역량분석:
    def test_부서별_평균(self) -> None:
        service, skill_repo, emp_repo = _make_service()
        emp_repo.find_many.return_value = [
            {"_id": "EMP-001", "department": "개발팀"},
            {"_id": "EMP-002", "department": "개발팀"},
        ]
        skill_repo.find_many.return_value = [
            {"employee": "EMP-001", "skills": {"Python": 5, "SQL": 3}},
            {"employee": "EMP-002", "skills": {"Python": 3, "SQL": 5}},
        ]

        result = service.get_department_skills("개발팀")

        assert result["employee_count"] == 2
        assert result["skill_averages"]["Python"] == 4.0  # (5+3)/2
        assert result["skill_averages"]["SQL"] == 4.0  # (3+5)/2


class Test필수교육확인:
    """BR-HR-016: 필수 교육 미수료 확인."""

    def test_미수료_과정_반환(self) -> None:
        """필수 과정 2개 중 1개만 수료한 경우 미수료 1개가 반환된다."""
        with patch("oneerp_hr_app.services.skill_map_service.Repository") as mock_repo_cls:
            # 미리 mock repo 생성하여 dict에 세팅
            course_repo = MagicMock()
            enrollment_repo = MagicMock()
            repos: dict[str, MagicMock] = {
                "learning_courses": course_repo,
                "learning_enrollments": enrollment_repo,
            }

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_hr_app.services.skill_map_service import SkillMapService

            service = SkillMapService(tenant_id="test-tenant")

            course_repo.find_many.return_value = [
                {"_id": "LCRSE-001", "course_name": "정보보안", "is_mandatory": True},
                {"_id": "LCRSE-002", "course_name": "성희롱예방", "is_mandatory": True},
            ]
            enrollment_repo.find_many.return_value = [
                {"employee_id": "EMP-001", "course_id": "LCRSE-001", "status": "completed"},
            ]

            result = service.check_mandatory_courses("EMP-001")

        assert result["all_completed"] is False
        assert len(result["incomplete_courses"]) == 1
        assert result["incomplete_courses"][0]["course_id"] == "LCRSE-002"

    def test_전체_수료(self) -> None:
        """모든 필수 과정을 수료한 경우 all_completed=True."""
        with patch("oneerp_hr_app.services.skill_map_service.Repository") as mock_repo_cls:
            course_repo = MagicMock()
            enrollment_repo = MagicMock()
            repos: dict[str, MagicMock] = {
                "learning_courses": course_repo,
                "learning_enrollments": enrollment_repo,
            }

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_hr_app.services.skill_map_service import SkillMapService

            service = SkillMapService(tenant_id="test-tenant")

            course_repo.find_many.return_value = [
                {"_id": "LCRSE-001", "course_name": "정보보안", "is_mandatory": True},
            ]
            enrollment_repo.find_many.return_value = [
                {"employee_id": "EMP-001", "course_id": "LCRSE-001", "status": "completed"},
            ]

            result = service.check_mandatory_courses("EMP-001")

        assert result["all_completed"] is True
        assert len(result["incomplete_courses"]) == 0

    def test_필수과정_없음(self) -> None:
        """필수 과정이 없으면 all_completed=True."""
        with patch("oneerp_hr_app.services.skill_map_service.Repository") as mock_repo_cls:
            course_repo = MagicMock()
            repos: dict[str, MagicMock] = {"learning_courses": course_repo}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_hr_app.services.skill_map_service import SkillMapService

            service = SkillMapService(tenant_id="test-tenant")

            course_repo.find_many.return_value = []

            result = service.check_mandatory_courses("EMP-001")

        assert result["all_completed"] is True
