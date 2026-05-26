"""채용 서비스 — 채용 파이프라인 (공고->지원->면접->합격->온보딩) 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-005: 채용 파이프라인 단계 순서 (applied->screening->interview->offered->accepted/rejected)
- BR-HR-013: 채용제안서 유효기한 (valid_until 경과 시 자동 만료)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from decimal import Decimal

from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 채용 파이프라인 상태
_PIPELINE_STAGES = ("applied", "screening", "interview", "offered", "accepted", "rejected")


class RecruitmentService:
    """채용 파이프라인 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._opening_repo = Repository("job_openings", tenant_id=tenant_id)
        self._applicant_repo = Repository("job_applicants", tenant_id=tenant_id)
        self._interview_repo = Repository("interview_rounds", tenant_id=tenant_id)
        self._feedback_repo = Repository("interview_feedbacks", tenant_id=tenant_id)
        self._offer_repo = Repository("offer_letters", tenant_id=tenant_id)

    def advance_applicant(
        self,
        applicant_id: str,
        next_stage: str,
    ) -> dict[str, Any]:
        """지원자를 다음 파이프라인 단계로 진행시킨다.

        Args:
            applicant_id: 지원자 ID
            next_stage: 다음 단계 (screening, interview, offered, accepted, rejected)

        Returns:
            진행 결과
        """
        applicant = self._applicant_repo.find_by_id(applicant_id)
        if not applicant:
            raise_not_found(f"지원자 '{applicant_id}'을 찾을 수 없습니다")

        if next_stage not in _PIPELINE_STAGES:
            raise_bad_request(f"유효하지 않은 단계입니다: {next_stage}")

        current_stage = applicant.get("stage", "applied")

        # BR-HR-005: 파이프라인 역방향 이동 차단
        current_index = _PIPELINE_STAGES.index(current_stage)
        next_index = _PIPELINE_STAGES.index(next_stage)
        if next_index <= current_index:
            raise_unprocessable("ERR-HR-033", "유효하지 않은 단계 이동입니다")

        self._applicant_repo.update_by_id(applicant_id, {"stage": next_stage})

        logger.info(
            "지원자 진행: %s (%s → %s)",
            applicant_id,
            current_stage,
            next_stage,
        )

        return {
            "applicant_id": applicant_id,
            "previous_stage": current_stage,
            "current_stage": next_stage,
        }

    def create_offer(
        self,
        applicant_id: str,
        designation: str,
        department: str,
        salary: Decimal,
    ) -> dict[str, Any]:
        """합격 통보서를 생성한다."""
        applicant = self._applicant_repo.find_by_id(applicant_id)
        if not applicant:
            raise_not_found(f"지원자 '{applicant_id}'을 찾을 수 없습니다")

        offer_id = generate_name("OFL", tenant_id=self._tenant_id)
        self._offer_repo.insert(
            {
                "_id": offer_id,
                "applicant": applicant_id,
                "applicant_name": applicant.get("applicant_name", ""),
                "designation": designation,
                "department": department,
                "salary": salary,
                "status": "pending",
                "tenant_id": self._tenant_id,
            }
        )

        # 지원자 상태를 offered로 변경
        self._applicant_repo.update_by_id(applicant_id, {"stage": "offered"})

        logger.info("합격 통보서 생성: %s (지원자: %s)", offer_id, applicant_id)

        return {
            "offer_id": offer_id,
            "applicant_id": applicant_id,
            "salary": salary,
        }

    def get_pipeline_summary(
        self,
        opening_id: str,
    ) -> dict[str, Any]:
        """채용 공고별 파이프라인 요약을 조회한다."""
        applicants = self._applicant_repo.find_many(
            {"job_opening": opening_id},
            limit=10000,
        )

        stage_counts: dict[str, int] = dict.fromkeys(_PIPELINE_STAGES, 0)
        for app in applicants:
            stage = app.get("stage", "applied")
            if stage in stage_counts:
                stage_counts[stage] += 1

        return {
            "opening_id": opening_id,
            "total_applicants": len(applicants),
            "stage_counts": stage_counts,
        }

    def expire_stale_offers(self) -> list[dict[str, Any]]:
        """BR-HR-013: 유효기한이 경과한 채용제안서를 만료 처리한다.

        offer_letters에서 status="pending"이고 valid_until < today인 건을
        status="expired"로 갱신한다.

        Returns:
            만료 처리된 채용제안서 목록
        """
        today = datetime.now(UTC).date().isoformat()

        pending_offers = self._offer_repo.find_many(
            {"status": "pending"},
            limit=10000,
        )

        expired: list[dict[str, Any]] = []
        for offer in pending_offers:
            valid_until = offer.get("valid_until", "")
            if not valid_until:
                continue
            if valid_until < today:
                self._offer_repo.update_by_id(offer["_id"], {"status": "expired"})
                expired.append(
                    {
                        "offer_id": offer["_id"],
                        "applicant": offer.get("applicant", ""),
                        "valid_until": valid_until,
                    }
                )

        logger.info("만료 처리된 채용제안서: %d건", len(expired))
        return expired
