"""성과 평가 서비스 - 평가 사이클 상태 머신 및 점수/등급 산정 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-025: 성과 평가 상태 머신
  DRAFT -> SELF_REVIEW -> MANAGER_REVIEW -> CALIBRATED -> COMPLETED
  역방향/건너뛰기 전이 금지 (무결성 보장)
- BR-HR-026: 점수 범위 [0.0, 5.0], 등급 자동 환산
  S: 4.5 이상, A: 4.0 이상, B: 3.0 이상, C: 2.0 이상, D: 2.0 미만
- BR-HR-027: 목표(Goal) 가중치 기반 종합 점수 산정
  score = sum(goal_score * goal_weight) / sum(goal_weight)
- BR-HR-028: 평가 사이클 내 동일 직원 중복 평가 금지
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 평가 상태 전이 그래프 (BR-HR-025)
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"self_review"},
    "self_review": {"manager_review"},
    "manager_review": {"calibrated"},
    "calibrated": {"completed"},
    "completed": set(),  # 종료 상태
}

# 점수 -> 등급 환산 테이블 (BR-HR-026) - 내림차순 조회
_GRADE_THRESHOLDS: list[tuple[Decimal, str]] = [
    (Decimal("4.5"), "S"),
    (Decimal("4.0"), "A"),
    (Decimal("3.0"), "B"),
    (Decimal("2.0"), "C"),
    (Decimal("0.0"), "D"),
]

_MIN_SCORE = Decimal("0.0")
_MAX_SCORE = Decimal("5.0")


class PerformanceAppraisalService:
    """성과 평가 비즈니스 로직.

    평가 상태 전이, 목표 기반 점수 계산, 등급 환산, 중복 방지를 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._appraisal_repo = Repository("appraisals", tenant_id=tenant_id)
        self._cycle_repo = Repository("appraisal_cycles", tenant_id=tenant_id)
        self._goal_repo = Repository("goal_settings", tenant_id=tenant_id)

    def create_appraisal(
        self,
        *,
        employee_id: str,
        appraisal_cycle_id: str,
        reviewer_id: str = "",
    ) -> dict[str, Any]:
        """BR-HR-028: 평가 사이클 내 중복 평가를 방지하며 평가를 생성한다.

        Args:
            employee_id: 평가 대상 직원
            appraisal_cycle_id: 평가 사이클 ID
            reviewer_id: 평가자 ID

        Returns:
            생성된 평가 문서 (status=draft)

        Raises:
            OneERPError: 동일 사이클·직원 평가가 이미 존재하는 경우
        """
        existing = self._appraisal_repo.find_many(
            {
                "employee_id": employee_id,
                "appraisal_cycle_id": appraisal_cycle_id,
            },
            limit=1,
        )
        if existing:
            raise_unprocessable(
                "ERR-HR-050",
                f"직원 '{employee_id}'의 평가가 사이클 '{appraisal_cycle_id}'에 이미 존재합니다",
            )

        doc = {
            "employee_id": employee_id,
            "appraisal_cycle_id": appraisal_cycle_id,
            "reviewer_id": reviewer_id,
            "status": "draft",
            "score": "0",
            "grade": "",
            "comments": "",
            "tenant_id": self._tenant_id,
        }
        self._appraisal_repo.insert(doc)

        logger.info(
            "평가 생성: 사이클 %s, 평가자 %s",
            appraisal_cycle_id,
            reviewer_id,
        )
        return doc

    def transition_status(
        self,
        appraisal_id: str,
        next_status: str,
    ) -> dict[str, Any]:
        """BR-HR-025: 평가 상태를 안전하게 전이한다.

        유효한 전이가 아니면 예외를 발생시키고, 완료 상태에서는 더 이상 전이할 수 없다.

        Args:
            appraisal_id: 평가 ID
            next_status: 다음 상태 ("self_review"/"manager_review"/"calibrated"/"completed")

        Returns:
            상태 전이 결과 dict (appraisal_id, from_status, to_status)

        Raises:
            OneERPError: 평가가 없거나 유효하지 않은 전이인 경우
        """
        appraisal = self._appraisal_repo.find_by_id(appraisal_id)
        if not appraisal:
            raise_not_found(f"평가 '{appraisal_id}'를 찾을 수 없습니다")

        current = str(appraisal.get("status", "draft"))
        allowed = _VALID_TRANSITIONS.get(current, set())
        if next_status not in allowed:
            raise_unprocessable(
                "ERR-HR-051",
                f"상태 전이 불가: {current} -> {next_status} (허용: {sorted(allowed) or '없음'})",
            )

        self._appraisal_repo.update_by_id(
            appraisal_id,
            {
                "status": next_status,
                "status_updated_at": datetime.now(UTC).isoformat(),
            },
        )

        logger.info("평가 상태 전이: %s (%s -> %s)", appraisal_id, current, next_status)
        return {
            "appraisal_id": appraisal_id,
            "from_status": current,
            "to_status": next_status,
        }

    def calculate_weighted_score(
        self,
        goals: list[dict[str, Any]],
    ) -> Decimal:
        """BR-HR-027: 목표 가중치 기반 종합 점수를 산정한다.

        공식: score = sum(goal_score * goal_weight) / sum(goal_weight)

        Args:
            goals: 목표 리스트 [{goal_score: float, weight: float}, ...]

        Returns:
            가중 평균 점수 (0.00~5.00, 소수 둘째 자리)

        Raises:
            OneERPError: 목표가 없거나 점수 범위를 벗어난 경우
        """
        if not goals:
            raise_unprocessable(
                "ERR-HR-052",
                "가중 점수를 계산하려면 목표(goals)가 1개 이상 있어야 합니다",
            )

        total_weighted = Decimal(0)
        total_weight = Decimal(0)

        for idx, g in enumerate(goals):
            raw_score = Decimal(str(g.get("goal_score", 0)))
            raw_weight = Decimal(str(g.get("weight", 0)))

            if raw_score < _MIN_SCORE or raw_score > _MAX_SCORE:
                raise_unprocessable(
                    "ERR-HR-053",
                    f"목표 {idx} 점수({raw_score})는 {_MIN_SCORE}~{_MAX_SCORE} 범위여야 합니다",
                )
            if raw_weight < 0:
                raise_unprocessable(
                    "ERR-HR-054",
                    f"목표 {idx} 가중치({raw_weight})는 0 이상이어야 합니다",
                )

            total_weighted += raw_score * raw_weight
            total_weight += raw_weight

        if total_weight == 0:
            raise_unprocessable(
                "ERR-HR-055",
                "목표 가중치 합계가 0입니다. 1개 이상의 목표에 가중치를 부여해야 합니다",
            )

        return (total_weighted / total_weight).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def score_to_grade(self, score: Decimal) -> str:
        """BR-HR-026: 점수를 등급(S/A/B/C/D)으로 환산한다.

        Args:
            score: 종합 점수 (0.0~5.0)

        Returns:
            등급 문자
        """
        score = Decimal(str(score))
        for threshold, grade in _GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "D"

    def finalize_score(
        self,
        appraisal_id: str,
        goals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """평가에 목표 기반 점수를 계산하여 저장하고 등급을 환산한다.

        반드시 manager_review 또는 calibrated 상태에서만 호출 가능.
        점수 반영 후 자동 전이는 하지 않으며, 별도로 transition_status를 호출해야 한다.

        Args:
            appraisal_id: 평가 ID
            goals: 목표 리스트 [{goal_score, weight}, ...]

        Returns:
            점수 확정 결과 dict (appraisal_id, score, grade)

        Raises:
            OneERPError: 평가가 없거나 유효하지 않은 상태인 경우
        """
        appraisal = self._appraisal_repo.find_by_id(appraisal_id)
        if not appraisal:
            raise_not_found(f"평가 '{appraisal_id}'를 찾을 수 없습니다")

        status = str(appraisal.get("status", "draft"))
        if status not in {"manager_review", "calibrated"}:
            raise_unprocessable(
                "ERR-HR-056",
                f"점수 확정은 manager_review/calibrated 상태에서만 가능합니다 (현재: {status})",
            )

        score = self.calculate_weighted_score(goals)
        grade = self.score_to_grade(score)

        self._appraisal_repo.update_by_id(
            appraisal_id,
            {"score": str(score), "grade": grade},
        )

        logger.info(
            "평가 점수 확정: %s (점수: %s, 등급: %s)",
            appraisal_id,
            score,
            grade,
        )
        return {
            "appraisal_id": appraisal_id,
            "score": str(score),
            "grade": grade,
        }
