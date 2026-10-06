"""역량 평가 서비스 — 직원 역량 매트릭스 관리 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-008: 역량 평가 점수 범위 (1~5점, 평균 자동 계산)
- BR-HR-015: 부서별 역량 집계 (직원별 역량 점수 평균)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class SkillMapService:
    """직원 역량 평가 매트릭스 비즈니스 로직.

    역량 평가, 부서별 역량 분석, 역량 갭 분석을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._skill_repo = Repository("employee_skill_maps", tenant_id=tenant_id)
        self._employee_repo = Repository("employees", tenant_id=tenant_id)

    def evaluate_skills(
        self,
        employee: str,
        skills: dict[str, int],
    ) -> dict[str, Any]:
        """직원의 역량을 평가한다.

        Args:
            employee: 직원 ID
            skills: 역량 이름 → 점수 (1~5) 매핑

        Returns:
            평가 결과 (average_score, skill_count)
        """
        if not skills:
            raise_unprocessable("ERR-HR-004", "역량을 1개 이상 평가해야 합니다")

        for name, score in skills.items():
            if not 1 <= score <= 5:
                raise_unprocessable(
                    "ERR-HR-005",
                    f"역량 '{name}' 점수({score})는 1~5 범위여야 합니다",
                )

        avg_score = round(sum(skills.values()) / len(skills), 2)

        # 기존 스킬맵 업데이트 또는 생성
        existing = self._skill_repo.find_many({"employee": employee}, limit=1)

        if existing:
            self._skill_repo.update_by_id(existing[0]["_id"], {"skills": skills})
        else:
            self._skill_repo.insert(
                {
                    "employee": employee,
                    "skills": skills,
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info(
            "역량 평가: 역량 %d개, 평균 %.2f",
            len(skills),
            avg_score,
        )

        return {
            "employee": employee,
            "skill_count": len(skills),
            "average_score": avg_score,
            "skills": skills,
        }

    def get_department_skills(
        self,
        department: str,
    ) -> dict[str, Any]:
        """부서별 역량 분석을 수행한다."""
        employees = self._employee_repo.find_many({"department": department}, limit=10000)
        emp_ids = [e.get("_id", "") for e in employees]

        skill_maps = self._skill_repo.find_many({}, limit=50000)
        dept_skills = [sm for sm in skill_maps if sm.get("employee") in emp_ids]

        # 역량별 평균 집계
        skill_totals: dict[str, list[int]] = {}
        for sm in dept_skills:
            for skill_name, score in sm.get("skills", {}).items():
                skill_totals.setdefault(skill_name, []).append(int(score))

        skill_averages = {
            name: round(sum(scores) / len(scores), 2) for name, scores in skill_totals.items()
        }

        return {
            "department": department,
            "employee_count": len(dept_skills),
            "skill_averages": skill_averages,
        }

    def check_mandatory_courses(
        self,
        employee_id: str,
    ) -> dict[str, Any]:
        """BR-HR-016: 직원의 필수 교육 미수료 목록을 반환한다.

        learning_courses에서 is_mandatory=true인 과정을 조회하고,
        learning_enrollments에서 해당 직원의 수료(completed) 여부를 확인한다.

        Args:
            employee_id: 직원 ID

        Returns:
            {
                "employee": str,
                "incomplete_courses": [{course_id, course_name}],
                "all_completed": bool,
            }
        """
        course_repo = Repository("learning_courses", tenant_id=self._tenant_id)
        enrollment_repo = Repository("learning_enrollments", tenant_id=self._tenant_id)

        # 필수 교육 과정 조회
        mandatory_courses = course_repo.find_many(
            {"is_mandatory": True},
            limit=10000,
        )

        if not mandatory_courses:
            return {
                "employee": employee_id,
                "incomplete_courses": [],
                "all_completed": True,
            }

        # 해당 직원의 수료 완료 등록 조회
        enrollments = enrollment_repo.find_many(
            {"employee_id": employee_id, "status": "completed"},
            limit=10000,
        )
        completed_course_ids = {e.get("course_id", "") for e in enrollments}

        # 미수료 과정 필터링
        incomplete: list[dict[str, str]] = []
        for course in mandatory_courses:
            course_id = course.get("_id", "")
            if course_id not in completed_course_ids:
                incomplete.append(
                    {
                        "course_id": course_id,
                        "course_name": course.get("course_name", ""),
                    }
                )

        logger.info(
            "필수 교육 미수료 확인: 미수료 %d건",
            len(incomplete),
        )

        return {
            "employee": employee_id,
            "incomplete_courses": incomplete,
            "all_completed": len(incomplete) == 0,
        }
