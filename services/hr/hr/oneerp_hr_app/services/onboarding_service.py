"""온보딩/오프보딩 서비스 — 체크리스트 기반 입퇴사 프로세스 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-006: 온보딩 체크리스트 진행률 = completed / total x 100
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class OnboardingService:
    """온보딩/오프보딩 체크리스트 비즈니스 로직.

    활동 목록의 완료 상태를 추적하고 전체 프로세스 진행률을 관리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._onboarding_repo = Repository("employee_onboardings", tenant_id=tenant_id)
        self._offboarding_repo = Repository("employee_offboardings", tenant_id=tenant_id)
        self._employee_repo = Repository("employees", tenant_id=tenant_id)

    def complete_activity(
        self,
        doc_id: str,
        activity_index: int,
        doc_type: str = "onboarding",
    ) -> dict[str, Any]:
        """활동을 완료 처리한다.

        Args:
            doc_id: 온보딩/오프보딩 문서 ID
            activity_index: 활동 인덱스 (0부터)
            doc_type: "onboarding" 또는 "offboarding"

        Returns:
            진행 상태 (progress, all_complete)
        """
        repo = self._onboarding_repo if doc_type == "onboarding" else self._offboarding_repo

        doc = repo.find_by_id(doc_id)
        if not doc:
            raise_not_found(
                f"{'온보딩' if doc_type == 'onboarding' else '오프보딩'} '{doc_id}'을 찾을 수 없습니다",
            )

        activities = doc.get("activities", [])
        if activity_index < 0 or activity_index >= len(activities):
            raise_unprocessable(
                "ERR-HR-002",
                f"활동 인덱스 {activity_index}가 범위를 벗어났습니다 (총 {len(activities)}개)",
            )

        # 활동 완료 처리
        activities[activity_index]["status"] = "completed"
        activities[activity_index]["completed_at"] = datetime.now(tz=UTC)

        repo.update_by_id(doc_id, {"activities": activities})

        # 진행률 계산
        completed = sum(1 for a in activities if a.get("status") == "completed")
        total = len(activities)
        all_complete = completed == total

        logger.info(
            "%s 활동 완료: %s (인덱스: %d, 진행: %d/%d)",
            doc_type,
            doc_id,
            activity_index,
            completed,
            total,
        )

        return {
            "doc_id": doc_id,
            "completed": completed,
            "total": total,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
            "all_complete": all_complete,
        }

    def get_progress(
        self,
        doc_id: str,
        doc_type: str = "onboarding",
    ) -> dict[str, Any]:
        """프로세스 진행 상태를 조회한다."""
        repo = self._onboarding_repo if doc_type == "onboarding" else self._offboarding_repo

        doc = repo.find_by_id(doc_id)
        if not doc:
            raise_not_found(f"문서 '{doc_id}'을 찾을 수 없습니다")

        activities = doc.get("activities", [])
        completed = sum(1 for a in activities if a.get("status") == "completed")
        total = len(activities)

        pending = [
            {"index": i, "task": a.get("task", ""), "responsible": a.get("responsible", "")}
            for i, a in enumerate(activities)
            if a.get("status") != "completed"
        ]

        return {
            "doc_id": doc_id,
            "employee": doc.get("employee", ""),
            "completed": completed,
            "total": total,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
            "pending_activities": pending,
        }
