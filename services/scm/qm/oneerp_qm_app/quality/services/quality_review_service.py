"""품질 검토 서비스 — 품질 검토, 조치, 메트릭 관리 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-QR-001: 자동 합격/불합격 판정 (모든 findings pass = 합격)
- BR-QR-002: 불합격 항목 조치 자동 생성
- BR-QR-003: 메트릭 목표 달성 판정 (value >= target)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from decimal import Decimal

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class QualityReviewService:
    """품질 검토 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._review_repo = Repository("quality_reviews", tenant_id=tenant_id)
        self._action_repo = Repository("quality_actions", tenant_id=tenant_id)
        self._metric_repo = Repository("quality_metrics", tenant_id=tenant_id)

    def create_review(
        self,
        document_type: str,
        document_id: str,
        inspector: str,
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """품질 검토를 생성한다."""
        review_id = generate_name("QR", tenant_id=self._tenant_id)
        passed = all(f.get("result") == "pass" for f in findings)

        self._review_repo.insert(
            {
                "_id": review_id,
                "document_type": document_type,
                "document_id": document_id,
                "inspector": inspector,
                "findings": findings,
                "status": "passed" if passed else "failed",
                "tenant_id": self._tenant_id,
            }
        )

        # 불합격 항목에 대해 조치 필요 플래그
        actions_needed = [f for f in findings if f.get("result") != "pass"]
        for finding in actions_needed:
            action_id = generate_name("QA", tenant_id=self._tenant_id)
            self._action_repo.insert(
                {
                    "_id": action_id,
                    "review_id": review_id,
                    "finding": finding.get("description", ""),
                    "status": "open",
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info(
            "품질 검토: %s (결과: %s, 조치 필요: %d건)",
            review_id,
            "합격" if passed else "불합격",
            len(actions_needed),
        )

        return {
            "review_id": review_id,
            "status": "passed" if passed else "failed",
            "finding_count": len(findings),
            "actions_needed": len(actions_needed),
        }

    def record_metric(
        self,
        metric_name: str,
        value: Decimal,
        target: Decimal,
        unit: str = "",
    ) -> dict[str, Any]:
        """품질 메트릭을 기록한다."""
        metric_id = generate_name("QM", tenant_id=self._tenant_id)
        meets_target = value >= target

        self._metric_repo.insert(
            {
                "_id": metric_id,
                "metric_name": metric_name,
                "value": value,
                "target": target,
                "unit": unit,
                "meets_target": meets_target,
                "tenant_id": self._tenant_id,
            }
        )

        return {
            "metric_id": metric_id,
            "metric_name": metric_name,
            "value": value,
            "target": target,
            "meets_target": meets_target,
        }
