"""캠페인 실행 서비스 — 캠페인 시작·일시정지·완료 및 성과 집계."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class CampaignExecutionService:
    """캠페인 실행 비즈니스 로직.

    캠페인 상태 전환, 성과 지표 집계, ROI 계산을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._campaign_repo = Repository("campaigns", tenant_id=tenant_id)
        self._analytics_repo = Repository("campaign_analytics", tenant_id=tenant_id)
        self._segment_repo = Repository("audience_segments", tenant_id=tenant_id)

    def start_campaign(self, campaign_id: str) -> dict[str, Any]:
        """캠페인을 시작한다.

        Args:
            campaign_id: 캠페인 ID

        Returns:
            시작 결과 (status, audience_count)

        Raises:
            ValueError: 캠페인 미존재 또는 시작 불가 상태
        """
        campaign = self._campaign_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"캠페인을 찾을 수 없습니다: {campaign_id}"
            raise ValueError(msg)

        current_status = campaign.get("status", "")
        if current_status not in ("draft", "scheduled", "paused"):
            msg = f"시작할 수 없는 상태입니다: {current_status}"
            raise ValueError(msg)

        # 타겟 오디언스 확인
        audience_id = campaign.get("target_audience_id", "")
        audience_count = 0
        if audience_id:
            segment = self._segment_repo.find_by_id(audience_id)
            if segment:
                audience_count = segment.get("member_count", 0)

        self._campaign_repo.update_by_id(
            campaign_id,
            {"status": "running"},
        )

        logger.info(
            "캠페인 시작: %s (오디언스: %d명)",
            campaign_id,
            audience_count,
        )

        return {
            "campaign_id": campaign_id,
            "status": "running",
            "audience_count": audience_count,
        }

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """캠페인을 일시정지한다."""
        campaign = self._campaign_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"캠페인을 찾을 수 없습니다: {campaign_id}"
            raise ValueError(msg)

        if campaign.get("status") != "running":
            msg = f"일시정지할 수 없는 상태입니다: {campaign.get('status')}"
            raise ValueError(msg)

        self._campaign_repo.update_by_id(campaign_id, {"status": "paused"})

        logger.info("캠페인 일시정지: %s", campaign_id)
        return {"campaign_id": campaign_id, "status": "paused"}

    def complete_campaign(self, campaign_id: str) -> dict[str, Any]:
        """캠페인을 완료한다."""
        campaign = self._campaign_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"캠페인을 찾을 수 없습니다: {campaign_id}"
            raise ValueError(msg)

        if campaign.get("status") not in ("running", "paused"):
            msg = f"완료할 수 없는 상태입니다: {campaign.get('status')}"
            raise ValueError(msg)

        # 성과 지표 집계
        metrics = self._aggregate_metrics(campaign_id)

        self._campaign_repo.update_by_id(
            campaign_id,
            {"status": "completed", "metrics": metrics},
        )

        logger.info("캠페인 완료: %s — 지표: %s", campaign_id, metrics)
        return {
            "campaign_id": campaign_id,
            "status": "completed",
            "metrics": metrics,
        }

    def get_campaign_roi(self, campaign_id: str) -> dict[str, Any]:
        """캠페인 ROI를 계산한다.

        Args:
            campaign_id: 캠페인 ID

        Returns:
            ROI 분석 결과 (budget, spent, revenue, roi_percent)

        Raises:
            ValueError: 캠페인 미존재
        """
        campaign = self._campaign_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"캠페인을 찾을 수 없습니다: {campaign_id}"
            raise ValueError(msg)

        budget = Decimal(str(campaign.get("budget", 0)))
        spent = Decimal(str(campaign.get("spent", 0)))
        metrics = self._aggregate_metrics(campaign_id)

        total_revenue = Decimal(str(metrics.get("total_revenue", 0)))

        roi_percent = Decimal(0)
        if spent > 0:
            roi_percent = ((total_revenue - spent) / spent * 100).quantize(Decimal("0.01"))

        return {
            "campaign_id": campaign_id,
            "budget": budget,
            "spent": spent,
            "total_revenue": total_revenue,
            "roi_percent": roi_percent,
            "metrics": metrics,
            "calculated_at": datetime.now(tz=UTC).isoformat(),
        }

    def _aggregate_metrics(self, campaign_id: str) -> dict[str, Any]:
        """캠페인 분석 이벤트를 집계한다."""
        events = self._analytics_repo.find_many(
            {"campaign_id": campaign_id},
            limit=10000,
        )

        counters: dict[str, int] = {}
        total_revenue = Decimal(0)

        for event in events:
            event_type = event.get("event_type", "unknown")
            counters[event_type] = counters.get(event_type, 0) + 1
            revenue = event.get("revenue_attributed", 0)
            total_revenue += Decimal(str(revenue))

        return {
            "impressions": counters.get("impression", 0),
            "clicks": counters.get("click", 0),
            "opens": counters.get("open", 0),
            "conversions": counters.get("conversion", 0),
            "bounces": counters.get("bounce", 0),
            "unsubscribes": counters.get("unsubscribe", 0),
            "total_events": len(events),
            "total_revenue": float(total_revenue),
        }
