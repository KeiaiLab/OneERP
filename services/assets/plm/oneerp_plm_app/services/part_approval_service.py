"""부품 승인 서비스 — 3중 검토(기술/품질/비용) 및 최종 승인 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

from oneerp_plm_app.models.part_approval import PartApprovalStatus

logger = logging.getLogger(__name__)


class PartApprovalService:
    """부품 승인 프로세스(PAP) 비즈니스 로직.

    기술·품질·비용 3중 검토 및 최종 승인을 담당���다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._approval_repo = Repository("part_approvals", tenant_id=tenant_id)

    def submit_technical_review(
        self,
        approval_id: str,
        reviewer_id: str,
        result: str,
        *,
        spec_compliance: bool = False,
        form_fit_function: bool = False,
        reliability_assessment: str = "",
        comments: str = "",
    ) -> dict[str, Any]:
        """기술 검토를 제출한다.

        Args:
            approval_id: 부품 승인 ID
            reviewer_id: 검토자 ID
            result: 검토 결과 (pass/fail/conditional)
            spec_compliance: 사양 적합 여부
            form_fit_function: 형상·적합·기능 호환 여부
            reliability_assessment: 신뢰성 평가 의견
            comments: 검토 의견

        Returns:
            검토 결과
        """
        approval = self._approval_repo.find_by_id(approval_id)
        if not approval:
            raise_not_found(f"부품 승인을 찾을 수 없습니다: {approval_id}")

        now = datetime.now(tz=UTC)
        technical_review = {
            "reviewer_id": reviewer_id,
            "result": result,
            "spec_compliance": spec_compliance,
            "form_fit_function": form_fit_function,
            "reliability_assessment": reliability_assessment,
            "comments": comments,
            "reviewed_at": now.isoformat(),
        }

        self._approval_repo.update_by_id(
            approval_id,
            {
                "technical_review": technical_review,
                "status": PartApprovalStatus.TECHNICAL_REVIEW.value,
            },
        )

        logger.info("부품 기술 검토 완료: approval=%s, result=%s", approval_id, result)
        return {"approval_id": approval_id, "review_type": "technical", "result": result}

    def submit_quality_review(
        self,
        approval_id: str,
        reviewer_id: str,
        result: str,
        *,
        incoming_inspection_plan: bool = False,
        supplier_quality_rating: str = "",
        rohs_compliance: bool = False,
        comments: str = "",
    ) -> dict[str, Any]:
        """품질 검토를 제출한다.

        Args:
            approval_id: 부품 승인 ID
            reviewer_id: 검토자 ID
            result: 검토 결과
            incoming_inspection_plan: 수입 검사 기준 수립 여부
            supplier_quality_rating: 공급사 품질 등급
            rohs_compliance: RoHS 적합 여부
            comments: 검토 의견

        Returns:
            검토 결과
        """
        approval = self._approval_repo.find_by_id(approval_id)
        if not approval:
            raise_not_found(f"부품 승인을 찾을 수 없습니다: {approval_id}")

        now = datetime.now(tz=UTC)
        quality_review = {
            "reviewer_id": reviewer_id,
            "result": result,
            "incoming_inspection_plan": incoming_inspection_plan,
            "supplier_quality_rating": supplier_quality_rating,
            "rohs_compliance": rohs_compliance,
            "comments": comments,
            "reviewed_at": now.isoformat(),
        }

        self._approval_repo.update_by_id(
            approval_id,
            {
                "quality_review": quality_review,
                "status": PartApprovalStatus.QUALITY_REVIEW.value,
            },
        )

        logger.info("부품 품질 검토 완료: approval=%s, result=%s", approval_id, result)
        return {"approval_id": approval_id, "review_type": "quality", "result": result}

    def submit_cost_review(
        self,
        approval_id: str,
        reviewer_id: str,
        result: str,
        unit_price: float = 0.0,
        moq: int = 0,
        lead_time_days: int = 0,
        price_compared_to_current: float = 0.0,
        comments: str = "",
    ) -> dict[str, Any]:
        """비용 검토를 제출한다.

        Args:
            approval_id: 부품 승인 ID
            reviewer_id: 검토자 ID
            result: 검토 결과
            unit_price: 단가
            moq: 최소 주문 수량
            lead_time_days: 리드타임(일)
            price_compared_to_current: 현재 부품 대비 가격 차이(%)
            comments: 검토 의견

        Returns:
            검토 결과
        """
        approval = self._approval_repo.find_by_id(approval_id)
        if not approval:
            raise_not_found(f"부품 승인을 찾을 수 없습니다: {approval_id}")

        now = datetime.now(tz=UTC)
        cost_review = {
            "reviewer_id": reviewer_id,
            "result": result,
            "unit_price": unit_price,
            "moq": moq,
            "lead_time_days": lead_time_days,
            "price_compared_to_current": price_compared_to_current,
            "comments": comments,
            "reviewed_at": now.isoformat(),
        }

        self._approval_repo.update_by_id(
            approval_id,
            {
                "cost_review": cost_review,
                "status": PartApprovalStatus.COST_REVIEW.value,
            },
        )

        logger.info("부품 비용 검토 완료: approval=%s, result=%s", approval_id, result)
        return {"approval_id": approval_id, "review_type": "cost", "result": result}

    def approve(
        self,
        approval_id: str,
        approved_by: str,
        conditions: str | None = None,
    ) -> dict[str, Any]:
        """부품을 최종 승인한다.

        3중 검토(기술/품질/비용)가 모두 pass여야 승인 가능하다.

        Args:
            approval_id: 부품 승인 ID
            approved_by: 승인자 ID
            conditions: 조건부 승인 시 조건 내용

        Returns:
            승인 결과
        """
        approval = self._approval_repo.find_by_id(approval_id)
        if not approval:
            raise_not_found(f"부품 승인을 찾을 수 없습니다: {approval_id}")

        # 3중 검토 완료 확인
        tech = approval.get("technical_review")
        qual = approval.get("quality_review")
        cost = approval.get("cost_review")

        review_status: dict[str, str] = {}
        if tech and tech.get("result") in ("pass", "conditional"):
            review_status["technical_review"] = tech["result"]
        else:
            review_status["technical_review"] = "미완료"

        if qual and qual.get("result") in ("pass", "conditional"):
            review_status["quality_review"] = qual["result"]
        else:
            review_status["quality_review"] = "미완료"

        if cost and cost.get("result") in ("pass", "conditional"):
            review_status["cost_review"] = cost["result"]
        else:
            review_status["cost_review"] = "미완료"

        incomplete = [k for k, v in review_status.items() if v == "미완료"]
        if incomplete:
            raise_bad_request(
                f"3중 검토가 모두 완료되어야 최종 승인이 가능합니다. 미완료: {incomplete}"
            )

        now = datetime.now(tz=UTC)
        final_status = PartApprovalStatus.CONDITIONAL if conditions else PartApprovalStatus.APPROVED

        self._approval_repo.update_by_id(
            approval_id,
            {
                "status": final_status.value,
                "approved_by": approved_by,
                "approved_at": now.isoformat(),
                "conditions": conditions,
            },
        )

        logger.info("부품 최종 승인: approval=%s, status=%s", approval_id, final_status.value)
        return {
            "approval_id": approval_id,
            "status": final_status.value,
            "approved_by": approved_by,
        }
