"""프로젝트 빌링 서비스 — 프로젝트 기반 청구 및 리소스 배정 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-PROJ-007: 자원 배정률 범위 (0~100%)
- BR-PROJ-014: 청구서 금액 = 리소스별 (hours x rate) 합산
- BR-PROJ-016: 일괄 인보이싱 대상 (docstatus=1, billed!=True)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ProjectBillingService:
    """프로젝트 빌링 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._project_repo = Repository("projects", tenant_id=tenant_id)
        self._billing_repo = Repository("project_billings", tenant_id=tenant_id)
        self._allocation_repo = Repository("resource_allocations", tenant_id=tenant_id)

    def generate_billing(
        self,
        project_id: str,
        billing_period: str,
    ) -> dict[str, Any]:
        """프로젝트 청구서를 생성한다.

        리소스 배정 시간 x 단가로 청구 금액을 계산.

        Args:
            project_id: 프로젝트 ID
            billing_period: 청구 기간 (예: "2026-03")

        Returns:
            청구 결과
        """
        project = self._project_repo.find_by_id(project_id)
        if not project:
            raise_not_found(f"프로젝트 '{project_id}'을 찾을 수 없습니다")

        # 리소스 배정 조회
        allocations = self._allocation_repo.find_many(
            {"project": project_id, "billing_period": billing_period},
            limit=10000,
        )

        line_items: list[dict[str, Any]] = []
        total = Decimal(0)
        for alloc in allocations:
            hours = Decimal(str(alloc.get("hours", 0)))
            rate = Decimal(str(alloc.get("hourly_rate", 0)))
            amount = hours * rate
            line_items.append(
                {
                    "resource": alloc.get("resource", ""),
                    "hours": hours,
                    "rate": rate,
                    "amount": amount,
                }
            )
            total += amount

        billing_id = generate_name("PBL", tenant_id=self._tenant_id)
        self._billing_repo.insert(
            {
                "_id": billing_id,
                "project": project_id,
                "billing_period": billing_period,
                "line_items": line_items,
                "total": total,
                "status": "draft",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "프로젝트 청구: 프로젝트 %s, 금액 %s",
            project_id,
            total,
        )

        return {
            "billing_id": billing_id,
            "project_id": project_id,
            "billing_period": billing_period,
            "total": total,
            "line_item_count": len(line_items),
        }
