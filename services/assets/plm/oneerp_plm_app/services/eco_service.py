"""ECO(설계 변경 요청) 서비스 — 변경 관리 워크플로우 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_plm_app.models.eng_change_notice import Acknowledgement, EngChangeNotice
from oneerp_plm_app.models.eng_change_order import ECO_TRANSITIONS, ECOStatus, ImpactAnalysis

logger = logging.getLogger(__name__)


class ECOService:
    """ECO 변경 관리 워크플로우 비즈니스 로직.

    ECO 제출, 검토자 배정, 검토, 승인, ECN 자동 생성을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._eco_repo = Repository("eng_change_orders", tenant_id=tenant_id)
        self._ecn_repo = Repository("eng_change_notices", tenant_id=tenant_id)
        self._bom_repo = Repository("bom_versions", tenant_id=tenant_id)
        self._drawing_repo = Repository("drawings", tenant_id=tenant_id)
        self._cert_repo = Repository("certifications", tenant_id=tenant_id)

    def submit_eco(self, eco_id: str) -> dict[str, Any]:
        """ECO를 제출한다 (draft → submitted).

        Args:
            eco_id: ECO ID

        Returns:
            제출 결과
        """
        eco = self._eco_repo.find_by_id(eco_id)
        if not eco:
            raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")

        status = ECOStatus(eco.get("status", "draft"))
        if ECOStatus.SUBMITTED not in ECO_TRANSITIONS.get(status, []):
            raise_bad_request(f"현재 상태({status.value})에서 제출할 수 없습니다")

        # 제출 조건 검증: 제안 변경 1개 이상
        if not eco.get("proposed_changes"):
            raise_bad_request("ECO 제출 조건 미충족: 제안 변경이 1개 이상 필요합니다")

        now = datetime.now(tz=UTC)
        self._eco_repo.update_by_id(
            eco_id,
            {
                "status": ECOStatus.SUBMITTED.value,
                "submitted_at": now.isoformat(),
            },
        )

        logger.info("ECO 제출 완료: eco=%s", eco_id)
        return {"eco_id": eco_id, "status": "submitted"}

    def assign_reviewers(
        self,
        eco_id: str,
        reviewers: list[dict[str, str]],
    ) -> dict[str, Any]:
        """ECO에 검토자를 배정하고 in_review 상태로 전환한다.

        Args:
            eco_id: ECO ID
            reviewers: 검토자 목록 [{"reviewer_id": "...", "review_role": "..."}]

        Returns:
            배정 결과
        """
        eco = self._eco_repo.find_by_id(eco_id)
        if not eco:
            raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")

        if not reviewers:
            raise_bad_request("검토자를 1명 이상 배정해야 합니다")

        reviewer_docs = [
            {
                "reviewer_id": r.get("reviewer_id", ""),
                "reviewer_name": r.get("reviewer_name", ""),
                "review_role": r.get("review_role", ""),
                "review_status": "pending",
                "review_comment": "",
                "reviewed_at": None,
            }
            for r in reviewers
        ]

        self._eco_repo.update_by_id(
            eco_id,
            {
                "reviewers": reviewer_docs,
                "status": ECOStatus.IN_REVIEW.value,
            },
        )

        logger.info("ECO 검토자 배정 완료: eco=%s, 검토자 수=%d", eco_id, len(reviewers))
        return {"eco_id": eco_id, "status": "in_review", "reviewer_count": len(reviewers)}

    def submit_review(
        self,
        eco_id: str,
        reviewer_id: str,
        review_status: str,
        review_comment: str = "",
    ) -> dict[str, Any]:
        """ECO 검토를 제출한다.

        Args:
            eco_id: ECO ID
            reviewer_id: 검토자 ID
            review_status: 검토 결과 (approved/rejected)
            review_comment: 검토 의견

        Returns:
            검토 결과
        """
        eco = self._eco_repo.find_by_id(eco_id)
        if not eco:
            raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")

        if eco.get("status") != ECOStatus.IN_REVIEW.value:
            raise_bad_request("in_review 상태에서만 검토 가능합니다")

        reviewers = eco.get("reviewers", [])
        found = False
        now = datetime.now(tz=UTC)
        for r in reviewers:
            if r.get("reviewer_id") == reviewer_id:
                r["review_status"] = review_status
                r["review_comment"] = review_comment
                r["reviewed_at"] = now.isoformat()
                found = True
                break

        if not found:
            raise_bad_request(f"배정된 검토자가 아닙니다: {reviewer_id}")

        self._eco_repo.update_by_id(eco_id, {"reviewers": reviewers})

        logger.info(
            "ECO 검토 제출: eco=%s, reviewer=%s, result=%s", eco_id, reviewer_id, review_status
        )
        return {"eco_id": eco_id, "reviewer_id": reviewer_id, "review_status": review_status}

    def approve_eco(
        self,
        eco_id: str,
        approved_by: str,
    ) -> dict[str, Any]:
        """ECO를 최종 승인하고 ECN을 자동 생성한다.

        Args:
            eco_id: ECO ID
            approved_by: 승인자 ID

        Returns:
            승인 결과 (ECN ID 포함)
        """
        eco = self._eco_repo.find_by_id(eco_id)
        if not eco:
            raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")

        if eco.get("status") != ECOStatus.IN_REVIEW.value:
            raise_bad_request("in_review 상태에서만 승인 가능합니다")

        # 모든 검토자 승인 확인 (긴급 ECO는 1명 이상)
        reviewers = eco.get("reviewers", [])
        is_emergency = eco.get("is_emergency", False)
        approved_count = sum(1 for r in reviewers if r.get("review_status") == "approved")
        rejected_count = sum(1 for r in reviewers if r.get("review_status") == "rejected")

        if rejected_count > 0:
            raise_bad_request("거부된 검토가 있어 승인할 수 없습니다")

        if is_emergency:
            if approved_count < 1:
                raise_bad_request("긴급 ECO는 최소 1명 이상 승인이 필요합니다")
        else:
            pending = sum(1 for r in reviewers if r.get("review_status") == "pending")
            if pending > 0:
                raise_bad_request(f"미완료 검토가 {pending}건 있습니다")

        # ECO 승인 처리
        now = datetime.now(tz=UTC)
        self._eco_repo.update_by_id(
            eco_id,
            {
                "status": ECOStatus.APPROVED.value,
                "approved_by": approved_by,
                "approved_at": now.isoformat(),
            },
        )

        # ECN 자동 생성
        ecn_id = generate_name("ECN", tenant_id=self._tenant_id)
        distribution = eco.get("affected_products", [])
        ecn = EngChangeNotice(
            _id=ecn_id,
            tenant_id=self._tenant_id,
            ecn_number=ecn_id,
            eco_id=eco_id,
            title=eco.get("title", ""),
            description=eco.get("description", ""),
            effective_date=eco.get("target_effective_date"),
            distribution_list=distribution,
            acknowledgements=[Acknowledgement(user_id=uid) for uid in distribution],
            issued_by=approved_by,
            issued_at=now,
            created_by=approved_by,
        )
        self._ecn_repo.insert(ecn)

        # ECO에 ECN 참조 갱신
        self._eco_repo.update_by_id(eco_id, {"ecn_id": ecn_id})

        logger.info("ECO 승인 및 ECN 생성 완료: eco=%s, ecn=%s", eco_id, ecn_id)
        return {
            "eco_id": eco_id,
            "status": "approved",
            "ecn_id": ecn_id,
        }

    def analyze_impact(self, eco_id: str) -> dict[str, Any]:
        """ECO 영향도를 분석한다.

        Args:
            eco_id: ECO ID

        Returns:
            영향도 분석 결과
        """
        eco = self._eco_repo.find_by_id(eco_id)
        if not eco:
            raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")

        affected_products = eco.get("affected_products", [])

        # 영향받는 BOM 수 집계
        bom_count = 0
        for pid in affected_products:
            boms = self._bom_repo.find({"product_id": pid})
            bom_count += len(list(boms))

        # 영향받는 도면 수 집계
        drawing_count = 0
        for pid in affected_products:
            drawings = self._drawing_repo.find({"product_id": pid})
            drawing_count += len(list(drawings))

        # 영향받는 인증 수 집계
        cert_count = 0
        for pid in affected_products:
            certs = self._cert_repo.find({"product_id": pid})
            cert_count += len(list(certs))

        # 위험 수준 결정
        total = bom_count + drawing_count + cert_count
        if total >= 10:
            risk_level = "critical"
        elif total >= 5:
            risk_level = "high"
        elif total >= 2:
            risk_level = "medium"
        else:
            risk_level = "low"

        now = datetime.now(tz=UTC)
        impact = ImpactAnalysis(
            affected_bom_count=bom_count,
            affected_drawing_count=drawing_count,
            affected_certification_count=cert_count,
            risk_level=risk_level,
            analyzed_at=now,
        )

        self._eco_repo.update_by_id(
            eco_id,
            {
                "impact_analysis": impact.model_dump(mode="json"),
            },
        )

        logger.info("ECO 영향도 분석 완료: eco=%s, risk=%s", eco_id, risk_level)
        return impact.model_dump(mode="json")
