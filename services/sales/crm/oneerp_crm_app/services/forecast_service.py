"""매출 예측 서비스 — 가중 파이프라인 기반 forecast.

L2 비즈니스 룰 매핑:
- BR-CRM-021: 가중 파이프라인 매출 예측 (expected_amount x probability)
- BR-CRM-022: forecast 카테고리 분류 (Commit/Best Case/Pipeline)
- BR-CRM-023: 단계별 정체 시간 기반 확률 감쇠 (stalled deal adjustment)

핵심 공식:
1. weighted_value = expected_amount x (probability / 100)
2. commit_forecast = Sum(weighted for deals at 90%+ probability)
3. best_case = Sum(weighted for deals at 60-89%)
4. pipeline = Sum(weighted for deals at 0-59%)
5. 정체 페널티: close_date 경과 또는 단계 진입 후 45일 이상 -> probability x 0.7

참고 베스트 프랙티스:
- Salesforce Forecast Categories: Commit (90%+), Best Case (60-89%), Pipeline (1-59%)
- Markov chain 기반 단계 전이 확률 (rework.com 2026 guide)
- Monte Carlo 시뮬레이션을 위한 누적 분포 산출 (relayco.io)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# Salesforce 표준 forecast 카테고리 임계값 (확률 %)
_CATEGORY_THRESHOLDS = [
    (Decimal(90), "commit"),  # 90% 이상
    (Decimal(60), "best_case"),  # 60~89%
    (Decimal(1), "pipeline"),  # 1~59%
]

# 단계별 정체 임계일 — 초과 시 확률 감쇠 적용
_STAGE_STALL_DAYS = 45

# 정체 페널티 계수 (0.7 = 30% 감소)
_STALL_PENALTY = Decimal("0.7")


@dataclass
class ForecastSummary:
    """forecast 집계 결과."""

    total_open_amount: Decimal
    weighted_total: Decimal
    commit: Decimal
    best_case: Decimal
    pipeline: Decimal
    deal_count: int
    stalled_count: int
    category_breakdown: list[dict[str, Any]] = field(default_factory=list)


class ForecastService:
    """매출 예측 서비스 — 가중 파이프라인 기반 forecast 집계."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._opp_repo = Repository("opportunities", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # BR-CRM-021: 가중 파이프라인 예측
    # ------------------------------------------------------------------

    def calculate_weighted_value(
        self,
        expected_amount: Decimal | float | int,
        probability: Decimal | float | int,
        close_date: date | None = None,
        stage_entered_at: datetime | None = None,
    ) -> dict[str, Any]:
        """단일 기회의 가중 기대값을 계산한다.

        수식: weighted_value = expected_amount x (probability / 100)
        정체 페널티: close_date 경과 또는 단계 진입 후 45일 초과 시 확률 x 0.7

        Args:
            expected_amount: 예상 금액
            probability: 원본 성사 확률 (0~100)
            close_date: 예상 성사일 (초과 시 감쇠)
            stage_entered_at: 현재 단계 진입 시각 (초과 시 감쇠)

        Returns:
            {"weighted_value", "adjusted_probability", "stalled", "original_probability"}
        """
        amount = Decimal(str(expected_amount))
        original_prob = Decimal(str(probability))

        adjusted_prob, stalled = self._adjust_probability(
            original_prob,
            close_date=close_date,
            stage_entered_at=stage_entered_at,
        )

        weighted = (amount * adjusted_prob / Decimal(100)).quantize(Decimal("0.01"))

        return {
            "expected_amount": float(amount),
            "original_probability": float(original_prob),
            "adjusted_probability": float(adjusted_prob),
            "weighted_value": float(weighted),
            "stalled": stalled,
        }

    def get_forecast_summary(
        self,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict[str, Any]:
        """BR-CRM-021/022: 기간별 forecast 요약을 집계한다.

        open/quotation 상태의 기회만 대상으로 한다.
        won/lost는 확정 매출이므로 forecast 대상이 아님.

        Args:
            period_start: 기간 시작일 (close_date 기준)
            period_end: 기간 종료일

        Returns:
            ForecastSummary를 dict로 변환
        """
        query: dict[str, Any] = {"status": {"$in": ["open", "quotation"]}}
        if period_start or period_end:
            close_filter: dict[str, Any] = {}
            if period_start:
                close_filter["$gte"] = period_start
            if period_end:
                close_filter["$lte"] = period_end
            query["close_date"] = close_filter

        opps = self._opp_repo.find_many(query, limit=10000)

        total_open = Decimal(0)
        weighted_total = Decimal(0)
        commit_sum = Decimal(0)
        best_case_sum = Decimal(0)
        pipeline_sum = Decimal(0)
        stalled_count = 0
        breakdown: list[dict[str, Any]] = []

        for opp in opps:
            amount = Decimal(str(opp.get("expected_amount", 0)))
            prob = Decimal(str(opp.get("probability", 0)))
            close_raw = opp.get("close_date")
            stage_entered_raw = opp.get("stage_entered_at")

            close_dt = self._to_date(close_raw)
            stage_dt = self._to_datetime(stage_entered_raw)

            adjusted_prob, stalled = self._adjust_probability(
                prob, close_date=close_dt, stage_entered_at=stage_dt
            )

            weighted = (amount * adjusted_prob / Decimal(100)).quantize(Decimal("0.01"))

            total_open += amount
            weighted_total += weighted

            category = self._categorize(adjusted_prob)
            if category == "commit":
                commit_sum += weighted
            elif category == "best_case":
                best_case_sum += weighted
            else:
                pipeline_sum += weighted

            if stalled:
                stalled_count += 1

            breakdown.append(
                {
                    "opportunity_id": opp.get("_id", ""),
                    "expected_amount": float(amount),
                    "adjusted_probability": float(adjusted_prob),
                    "weighted_value": float(weighted),
                    "category": category,
                    "stalled": stalled,
                }
            )

        summary = ForecastSummary(
            total_open_amount=total_open,
            weighted_total=weighted_total.quantize(Decimal("0.01")),
            commit=commit_sum.quantize(Decimal("0.01")),
            best_case=best_case_sum.quantize(Decimal("0.01")),
            pipeline=pipeline_sum.quantize(Decimal("0.01")),
            deal_count=len(opps),
            stalled_count=stalled_count,
            category_breakdown=breakdown,
        )

        logger.info(
            "forecast 집계: deals=%d, weighted=%s, commit=%s, best_case=%s, pipeline=%s, stalled=%d",
            summary.deal_count,
            summary.weighted_total,
            summary.commit,
            summary.best_case,
            summary.pipeline,
            summary.stalled_count,
        )

        return {
            "deal_count": summary.deal_count,
            "total_open_amount": float(summary.total_open_amount),
            "weighted_total": float(summary.weighted_total),
            "commit": float(summary.commit),
            "best_case": float(summary.best_case),
            "pipeline": float(summary.pipeline),
            "stalled_count": summary.stalled_count,
            "breakdown": summary.category_breakdown,
        }

    def get_pipeline_velocity(self) -> dict[str, Any]:
        """단계 평균 체류 시간과 전환 속도를 집계한다.

        Pipeline Velocity = (won_opportunities x avg_deal_size x win_rate) / avg_sales_cycle_days

        Returns:
            {"velocity_score", "win_rate", "avg_deal_size", "won_count", "open_count"}
        """
        won_opps = self._opp_repo.find_many({"status": "won"}, limit=10000)
        all_opps = self._opp_repo.find_many({}, limit=10000)
        open_opps = [o for o in all_opps if o.get("status") in ("open", "quotation")]

        won_count = len(won_opps)
        total_count = len(all_opps)
        open_count = len(open_opps)

        win_rate = (
            Decimal(won_count) / Decimal(total_count) * Decimal(100)
            if total_count > 0
            else Decimal(0)
        )

        avg_deal_size = Decimal(0)
        if won_count > 0:
            total_won_amount = sum(Decimal(str(o.get("expected_amount", 0))) for o in won_opps)
            avg_deal_size = total_won_amount / Decimal(won_count)

        # 평균 영업 사이클(일) — 데이터 부재 시 보수적 30일 기본
        avg_cycle_days = self._average_cycle_days(won_opps)

        velocity = Decimal(0)
        if avg_cycle_days > 0:
            velocity = (
                Decimal(won_count)
                * avg_deal_size
                * win_rate
                / Decimal(100)
                / Decimal(avg_cycle_days)
            )

        return {
            "velocity_score": float(velocity.quantize(Decimal("0.01"))),
            "win_rate": float(win_rate.quantize(Decimal("0.01"))),
            "avg_deal_size": float(avg_deal_size.quantize(Decimal("0.01"))),
            "won_count": won_count,
            "open_count": open_count,
            "avg_cycle_days": avg_cycle_days,
        }

    # ------------------------------------------------------------------
    # BR-CRM-023: 정체 deal 확률 감쇠
    # ------------------------------------------------------------------

    def _adjust_probability(
        self,
        probability: Decimal,
        close_date: date | None,
        stage_entered_at: datetime | None,
    ) -> tuple[Decimal, bool]:
        """정체(stalled) deal의 확률을 감쇠한다.

        감쇠 조건:
        - close_date가 오늘보다 이전
        - stage_entered_at이 45일 이상 이전
        감쇠 적용 시 probability x 0.7, 최대 100% 제한.
        """
        today = datetime.now(tz=UTC).date()
        stalled = False

        if close_date and close_date < today:
            stalled = True

        if stage_entered_at and (datetime.now(tz=UTC) - stage_entered_at).days > _STAGE_STALL_DAYS:
            stalled = True

        if stalled:
            adjusted = (probability * _STALL_PENALTY).quantize(Decimal("0.01"))
            return adjusted, True

        return probability.quantize(Decimal("0.01")), False

    def _categorize(self, probability: Decimal) -> str:
        """확률을 forecast 카테고리로 분류한다."""
        for threshold, category in _CATEGORY_THRESHOLDS:
            if probability >= threshold:
                return category
        return "omitted"

    def _average_cycle_days(self, won_opps: list[dict[str, Any]]) -> int:
        """성사 기회의 평균 영업 사이클(일)을 계산한다."""
        cycles: list[int] = []
        for opp in won_opps:
            created = self._to_datetime(opp.get("created_at"))
            closed = self._to_datetime(opp.get("closed_at") or opp.get("updated_at"))
            if created and closed:
                days = (closed - created).days
                if days > 0:
                    cycles.append(days)
        if not cycles:
            return 30  # 보수적 기본값
        return max(1, sum(cycles) // len(cycles))

    def _to_date(self, value: Any) -> date | None:
        """값을 date로 변환한다."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _to_datetime(self, value: Any) -> datetime | None:
        """값을 datetime으로 변환한다."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time(), tzinfo=UTC)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except ValueError:
                return None
        return None
