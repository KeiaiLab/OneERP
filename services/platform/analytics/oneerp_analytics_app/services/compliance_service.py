"""컴플라이언스 서비스 — 내부통제, 위험평가, 감사 추적 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ComplianceService:
    """컴플라이언스 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._audit_repo = Repository("audit_trails", tenant_id=tenant_id)
        self._control_repo = Repository("internal_controls", tenant_id=tenant_id)
        self._checklist_repo = Repository("compliance_checklists", tenant_id=tenant_id)
        self._risk_repo = Repository("risk_assessments", tenant_id=tenant_id)
        self._report_repo = Repository("compliance_reports", tenant_id=tenant_id)

    def create_risk_assessment(
        self,
        area: str,
        risks: list[dict[str, Any]],
        assessor: str,
    ) -> dict[str, Any]:
        """위험평가를 생성한다."""
        risk_id = generate_name("RA", tenant_id=self._tenant_id)

        # 각 위험 항목에 위험도 점수 계산 (확률 x 영향)
        for risk in risks:
            probability = float(risk.get("probability", 1))
            impact = float(risk.get("impact", 1))
            risk["risk_score"] = round(probability * impact, 2)

        overall_score = round(sum(r["risk_score"] for r in risks) / len(risks), 2) if risks else 0.0

        self._risk_repo.insert(
            {
                "_id": risk_id,
                "area": area,
                "assessor": assessor,
                "risks": risks,
                "overall_risk_score": overall_score,
                "risk_level": "high"
                if overall_score > 15
                else "medium"
                if overall_score > 8
                else "low",
                "status": "draft",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "위험평가 생성: %s (영역: %s, 위험수준: %s)",
            risk_id,
            area,
            "high" if overall_score > 15 else "low",
        )

        return {
            "risk_assessment_id": risk_id,
            "area": area,
            "overall_risk_score": overall_score,
            "risk_count": len(risks),
        }

    def generate_compliance_report(
        self,
        period: str,
    ) -> dict[str, Any]:
        """컴플라이언스 보고서를 생성한다."""
        # 해당 기간의 감사 이력 수
        audits = self._audit_repo.find_many({}, limit=50000)
        controls = self._control_repo.find_many({"is_active": True}, limit=1000)
        risks = self._risk_repo.find_many({}, limit=1000)

        high_risks = [r for r in risks if r.get("risk_level") == "high"]

        report_id = generate_name("CR", tenant_id=self._tenant_id)
        self._report_repo.insert(
            {
                "_id": report_id,
                "period": period,
                "audit_count": len(audits),
                "active_controls": len(controls),
                "total_risks": len(risks),
                "high_risks": len(high_risks),
                "status": "draft",
                "tenant_id": self._tenant_id,
            }
        )

        return {
            "report_id": report_id,
            "period": period,
            "audit_count": len(audits),
            "active_controls": len(controls),
            "high_risk_count": len(high_risks),
        }
