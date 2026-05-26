"""프로젝트 원가 서비스 — 원가 계산 및 수익성 분석.

L2 비즈니스 룰 매핑:
- BR-PROJ-012: 프로젝트 원가 = 인건비 + 자재비 + 경비
- BR-PROJ-013: 프로젝트 수익률 계산
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ProjectCostService:
    """프로젝트 원가 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._project_repo = Repository("projects", tenant_id=tenant_id)
        self._ts_repo = Repository("timesheets", tenant_id=tenant_id)
        self._alloc_repo = Repository("resource_allocations", tenant_id=tenant_id)
        self._billing_repo = Repository("project_billings", tenant_id=tenant_id)

    def calculate_project_cost(self, project_id: str) -> dict[str, Any]:
        """프로젝트 총 원가를 계산한다.

        인건비(타임시트 hours * hourly_rate) + 자재비 + 경비를 합산한다.
        """
        project = self._project_repo.find_by_id(project_id)
        if not project:
            raise_not_found(f"프로젝트 '{project_id}'을 찾을 수 없습니다")

        # 인건비: 리소스 배정의 hours * hourly_rate
        allocations = self._alloc_repo.find_many(
            {"project": project_id},
            limit=10000,
        )
        labor_cost = sum(
            (Decimal(str(a.get("hours", 0))) * Decimal(str(a.get("hourly_rate", 0))))
            for a in allocations
        )

        # 자재비/경비: 리소스 배정에서 type별 분류
        material_cost = sum(
            Decimal(str(a.get("amount", 0))) for a in allocations if a.get("type") == "material"
        )
        expense_cost = sum(
            Decimal(str(a.get("amount", 0))) for a in allocations if a.get("type") == "expense"
        )

        total = labor_cost + material_cost + expense_cost

        logger.info("프로젝트 원가: %s = %s원", project_id, total)
        return {
            "project_id": project_id,
            "labor_cost": labor_cost,
            "material_cost": material_cost,
            "expense_cost": expense_cost,
            "total_cost": total,
        }

    def get_profitability(self, project_id: str) -> dict[str, Any]:
        """프로젝트 수익성을 분석한다.

        수익률 = (매출 - 원가) / 매출 * 100
        """
        project = self._project_repo.find_by_id(project_id)
        if not project:
            raise_not_found(f"프로젝트 '{project_id}'을 찾을 수 없습니다")

        # 매출: 청구 합계
        billings = self._billing_repo.find_many(
            {"project": project_id},
            limit=10000,
        )
        revenue = sum(Decimal(str(b.get("total", 0))) for b in billings)

        # 원가 계산
        cost_data = self.calculate_project_cost(project_id)
        total_cost = cost_data["total_cost"]

        # 수익률
        if revenue > 0:
            margin = (revenue - total_cost) / revenue * Decimal(100)
            margin = margin.quantize(Decimal("0.01"))
        else:
            margin = Decimal(0)

        profit = revenue - total_cost

        logger.info("프로젝트 수익성: %s — 수익률 %s%%", project_id, margin)
        return {
            "project_id": project_id,
            "revenue": revenue,
            "total_cost": total_cost,
            "profit": profit,
            "margin_percent": margin,
        }
