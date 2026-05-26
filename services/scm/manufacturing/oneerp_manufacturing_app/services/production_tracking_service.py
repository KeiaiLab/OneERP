"""생산 추적 서비스 — 진행률/공정손실/OEE/차이분석.

L2 비즈니스 룰 매핑:
- BR-MFG-016: OEE = 가용률 x 성능률 x 양품률
- BR-MFG-017: 공정 손실률 = (expected - actual) / expected x 100
- BR-MFG-018: 차이 분석 = (produced - planned) / planned x 100
"""

from __future__ import annotations

import calendar
import logging
import re
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def _parse_period(period: str) -> tuple[str, str]:
    """기간 문자열을 ISO 날짜 범위(시작, 종료)로 변환한다.

    지원 형식:
    - "YYYY-MM" → 해당 월 1일 ~ 말일
    - "YYYY-QN" → 해당 분기 시작 ~ 종료
    - 그 외 → 현재 월 1일 ~ 말일
    """
    # YYYY-MM 형식
    m = re.match(r"^(\d{4})-(\d{2})$", period)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"

    # YYYY-QN 형식 (Q1~Q4)
    m = re.match(r"^(\d{4})-Q([1-4])$", period)
    if m:
        year, quarter = int(m.group(1)), int(m.group(2))
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        last_day = calendar.monthrange(year, end_month)[1]
        return (
            f"{year:04d}-{start_month:02d}-01",
            f"{year:04d}-{end_month:02d}-{last_day:02d}",
        )

    # 그 외 → 현재 월
    today = datetime.now(tz=UTC).date()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return (
        f"{today.year:04d}-{today.month:02d}-01",
        f"{today.year:04d}-{today.month:02d}-{last_day:02d}",
    )


class ProductionTrackingService:
    """생산 추적 비즈니스 로직.

    작업지시 진행률 조회, 공정 손실 기록,
    OEE(설비종합효율) 산출, 계획 대비 실적 차이 분석.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)
        self._loss_repo = Repository("process_losses", tenant_id=tenant_id)
        self._oee_repo = Repository("oee_metrics", tenant_id=tenant_id)
        self._downtime_repo = Repository("downtime_entries", tenant_id=tenant_id)
        self._variance_repo = Repository(
            "production_variance_analyses",
            tenant_id=tenant_id,
        )

    def get_progress(self, work_order_id: str) -> dict[str, Any]:
        """작업지시 진행률을 계산한다.

        Args:
            work_order_id: 작업지시 ID

        Returns:
            {work_order_id, planned_qty, produced_qty, progress_pct}
        """
        wo = self._wo_repo.find_by_id(work_order_id)
        if not wo:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-003",
                detail=f"작업지시 '{work_order_id}'을 찾을 수 없습니다",
            )

        planned = float(wo.get("planned_qty", 0))
        produced = float(wo.get("produced_qty", 0))
        progress = (produced / planned * 100) if planned > 0 else 0.0

        return {
            "work_order_id": work_order_id,
            "planned_qty": planned,
            "produced_qty": produced,
            "progress_pct": round(progress, 2),
        }

    def record_process_loss(
        self,
        work_order_id: str,
        item_code: str,
        expected_qty: float,
        actual_qty: float,
    ) -> dict[str, Any]:
        """BR-MFG-017: 공정 손실률 = (expected - actual) / expected x 100.

        Args:
            work_order_id: 작업지시 ID
            item_code: 자재 코드
            expected_qty: 예상 수량
            actual_qty: 실제 수량

        Returns:
            생성된 공정 손실 문서
        """
        loss_qty = expected_qty - actual_qty
        loss_pct = (loss_qty / expected_qty * 100) if expected_qty > 0 else 0.0

        loss_id = generate_name("PLSS", tenant_id=self._tenant_id)
        loss_doc = {
            "_id": loss_id,
            "work_order_id": work_order_id,
            "item_code": item_code,
            "expected_qty": expected_qty,
            "actual_qty": actual_qty,
            "loss_qty": loss_qty,
            "loss_percentage": round(loss_pct, 2),
            "tenant_id": self._tenant_id,
        }
        self._loss_repo.insert(loss_doc)

        logger.info(
            "공정 손실 기록: %s (품목: %s, 손실률: %.2f%%)",
            loss_id,
            item_code,
            loss_pct,
        )
        return loss_doc

    def calculate_oee(
        self,
        workstation_id: str,
        period: str,
    ) -> dict[str, Any]:
        """BR-MFG-016: OEE(설비종합효율) = 가용률 x 성능률 x 양품률.

        소수점 4자리 반올림 저장.

        Args:
            workstation_id: 작업장 ID
            period: 기간 (예: "2026-03")

        Returns:
            {workstation_id, period, availability, performance, quality_rate, oee}
        """
        # period 문자열을 날짜 범위로 변환
        period_start, period_end = _parse_period(period)

        # 비가동 시간 합산 (start_time 기준 필터링)
        downtimes = self._downtime_repo.find_many(
            {
                "workstation_id": workstation_id,
                "start_time": {"$gte": period_start, "$lte": period_end},
            },
            limit=100,
        )
        total_downtime = sum(float(d.get("duration_minutes", 0)) for d in downtimes)

        # 기본 가용 시간 (월 기준 480분/일 x 22일 = 10560분)
        total_available_minutes = 10560.0
        actual_run_minutes = total_available_minutes - total_downtime
        availability = (
            actual_run_minutes / total_available_minutes if total_available_minutes > 0 else 0.0
        )

        # 해당 작업장의 작업지시에서 성능·양품률 산출 (planned_start_date 기준 필터링)
        work_orders = self._wo_repo.find_many(
            {
                "workstation_id": workstation_id,
                "planned_start_date": {"$gte": period_start, "$lte": period_end},
            },
            limit=100,
        )
        total_planned = sum(float(w.get("planned_qty", 0)) for w in work_orders)
        total_produced = sum(float(w.get("produced_qty", 0)) for w in work_orders)
        total_loss = sum(float(w.get("process_loss_qty", 0)) for w in work_orders)

        performance = (total_produced / total_planned) if total_planned > 0 else 0.0
        good_qty = total_produced - total_loss
        quality_rate = (good_qty / total_produced) if total_produced > 0 else 0.0

        oee = availability * performance * quality_rate

        # OEE 지표 저장
        oee_id = generate_name("OEE", tenant_id=self._tenant_id)
        result = {
            "_id": oee_id,
            "workstation_id": workstation_id,
            "period": period,
            "availability": round(availability, 4),
            "performance": round(performance, 4),
            "quality_rate": round(quality_rate, 4),
            "oee": round(oee, 4),
            "tenant_id": self._tenant_id,
        }
        self._oee_repo.insert(result)

        logger.info(
            "OEE 산출: %s (가용: %.2f, 성능: %.2f, 품질: %.2f, OEE: %.2f)",
            workstation_id,
            availability,
            performance,
            quality_rate,
            oee,
        )
        return result

    def analyze_variance(self, work_order_id: str) -> dict[str, Any]:
        """BR-MFG-018: 계획 대비 실적 차이 분석 (양수=초과달성, 음수=미달).

        Args:
            work_order_id: 작업지시 ID

        Returns:
            {work_order_id, planned_qty, produced_qty, variance, variance_pct}
        """
        wo = self._wo_repo.find_by_id(work_order_id)
        if not wo:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-003",
                detail=f"작업지시 '{work_order_id}'을 찾을 수 없습니다",
            )

        planned = float(wo.get("planned_qty", 0))
        produced = float(wo.get("produced_qty", 0))
        variance = produced - planned
        variance_pct = (variance / planned * 100) if planned > 0 else 0.0

        # 차이 분석 결과 저장
        pva_id = generate_name("PVA", tenant_id=self._tenant_id)
        result = {
            "_id": pva_id,
            "work_order_id": work_order_id,
            "planned_qty": planned,
            "produced_qty": produced,
            "variance": variance,
            "variance_percentage": round(variance_pct, 2),
            "tenant_id": self._tenant_id,
        }
        self._variance_repo.insert(result)

        logger.info(
            "차이 분석: %s (계획: %s, 실적: %s, 차이: %.2f%%)",
            work_order_id,
            planned,
            produced,
            variance_pct,
        )
        return result
