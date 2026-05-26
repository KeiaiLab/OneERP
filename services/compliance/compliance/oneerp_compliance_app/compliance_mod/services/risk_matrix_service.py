"""위험 매트릭스 서비스 — 위험 평가 데이터 기반 매트릭스 분석."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class RiskMatrixService:
    """위험 매트릭스 분석 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._risk_repo = Repository("risk_assessments", tenant_id=tenant_id)

    def generate_matrix(self) -> dict[str, Any]:
        """위험 매트릭스를 생성한다.

        가능성(1-5) x 영향도(1-5) 매트릭스를 구성하고,
        각 셀에 해당하는 위험 항목 수를 반환한다.
        """
        assessments = self._risk_repo.find_many()

        # 5x5 매트릭스 초기화
        matrix: dict[str, int] = {}
        for likelihood in range(1, 6):
            for impact in range(1, 6):
                matrix[f"{likelihood}x{impact}"] = 0

        high_risks: list[dict[str, Any]] = []

        for assessment in assessments:
            likelihood = assessment.get("likelihood", 1)
            impact = assessment.get("impact", 1)
            key = f"{likelihood}x{impact}"
            if key in matrix:
                matrix[key] += 1

            # 고위험 항목 (점수 >= 15)
            score = likelihood * impact
            if score >= 15:
                high_risks.append(
                    {
                        "risk_name": assessment.get("risk_name", ""),
                        "likelihood": likelihood,
                        "impact": impact,
                        "score": score,
                    }
                )

        logger.info(
            "위험 매트릭스 생성: 전체 %d건, 고위험 %d건",
            len(assessments),
            len(high_risks),
        )

        return {
            "matrix": matrix,
            "total_assessments": len(assessments),
            "high_risks": high_risks,
            "high_risk_count": len(high_risks),
        }
