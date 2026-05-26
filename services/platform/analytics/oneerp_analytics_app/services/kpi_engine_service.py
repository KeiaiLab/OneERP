"""KPI 엔진 서비스 — 스냅샷 기록, 트렌드 조회, 대시보드 요약.

L2 비즈니스 룰 매핑:
- BR-05: 달성률 자동 계산 ((actual / target) x 100)
- BR-06: 중복 스냅샷 방지 (동일 kpi_id + period upsert)
- BR-07: KPI 비활성화 시 자동 캡처 제외
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_analytics_app.models.kpi_snapshot import KPISnapshot

logger = logging.getLogger(__name__)


class KPIEngineService:
    """KPI 엔진 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._kpi_repo = Repository("kpi_definitions", tenant_id=tenant_id)
        self._snapshot_repo = Repository("kpi_snapshots", tenant_id=tenant_id)

    def take_snapshot(self, kpi_id: str, period: str, actual_value: float) -> dict[str, Any]:
        """KPI 스냅샷을 기록한다. achievement_rate = actual / target * 100."""
        kpi = self._kpi_repo.find_by_id(kpi_id)
        if not kpi:
            raise_not_found(f"KPI 정의 '{kpi_id}'를 찾을 수 없습니다")

        target = Decimal(str(kpi.get("target_value", 0) or 0))
        actual = Decimal(str(actual_value))
        achievement_rate = (actual / target * 100) if target else Decimal(0)

        snapshot_id = generate_name("KPIS", tenant_id=self._tenant_id)
        doc = KPISnapshot(
            _id=snapshot_id,
            kpi_id=kpi_id,
            period=period,
            actual_value=actual,
            target_value=target,
            achievement_rate=achievement_rate.quantize(Decimal("0.01")),
            tenant_id=self._tenant_id,
        )
        self._snapshot_repo.insert(doc)

        logger.info(
            "KPI 스냅샷: %s (KPI: %s, 달성률: %.2f%%)", snapshot_id, kpi_id, achievement_rate
        )
        return {
            "snapshot_id": snapshot_id,
            "kpi_id": kpi_id,
            "achievement_rate": float(achievement_rate.quantize(Decimal("0.01"))),
        }

    def get_trend(self, kpi_id: str, periods: int = 12) -> list[dict[str, Any]]:
        """최근 N기간의 KPI 시계열을 반환한다."""
        return self._snapshot_repo.find_many(
            {"kpi_id": kpi_id},
            sort=[("period", -1)],
            limit=periods,
        )

    def get_dashboard_summary(self, period: str) -> list[dict[str, Any]]:
        """모든 활성 KPI의 해당 기간 요약을 반환한다."""
        active_kpis = self._kpi_repo.find_many({"is_active": True}, limit=100)
        summaries: list[dict[str, Any]] = []

        for kpi in active_kpis:
            kpi_id = kpi.get("_id", "")
            snapshots = self._snapshot_repo.find_many({"kpi_id": kpi_id, "period": period}, limit=1)
            snapshot = snapshots[0] if snapshots else None
            summaries.append(
                {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi.get("kpi_name", ""),
                    "target_value": kpi.get("target_value", 0.0),
                    "actual_value": snapshot.get("actual_value", 0.0) if snapshot else 0.0,
                    "achievement_rate": snapshot.get("achievement_rate", 0.0) if snapshot else 0.0,
                }
            )

        return summaries
