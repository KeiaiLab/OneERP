"""고객 생애 가치(CLV) + 이탈 위험 평가 서비스.

L2 비즈니스 룰 매핑:
- BR-CRM-024: 고객 생애 가치(Customer Lifetime Value) 계산
- BR-CRM-025: 이탈 위험(Churn Risk) 점수 산출
- BR-CRM-026: CLV 등급 및 이탈 위험 분류

핵심 공식:
1. CLV = avg_order_value x purchase_frequency x customer_lifespan_months
2. avg_order_value = total_revenue / order_count
3. purchase_frequency = order_count / 관측 기간(개월)
4. customer_lifespan = (현재 - 첫 거래일) / 30일
5. churn_risk_score = 0~100 (최근 거래 갭 기반)
   - 30일 이내: 0 (정상)
   - 30~60일: 25 (관찰)
   - 60~90일: 50 (주의)
   - 90~180일: 75 (위험)
   - 180일 초과: 100 (이탈)

참고 베스트 프랙티스:
- monday.com 2026 CLV 가이드: avg_order x frequency x lifespan
- Nature 2025: 특성 공학으로 churn 예측 정확도 85~92%
- expressanalytics.com: 세분화된 segment별 churn 모델
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# CLV 등급 임계값 (원화 기준)
_CLV_TIERS = [
    (Decimal(100000000), "platinum"),  # 1억 이상
    (Decimal(30000000), "gold"),  # 3000만~1억
    (Decimal(10000000), "silver"),  # 1000만~3000만
    (Decimal(1000000), "bronze"),  # 100만~1000만
]

# 이탈 위험 등급 — 최근 거래 갭(일) 기준
_CHURN_TIERS = [
    (180, 100, "churned"),  # 6개월 초과 -> 이탈
    (90, 75, "at_risk"),  # 3~6개월 -> 위험
    (60, 50, "warning"),  # 2~3개월 -> 주의
    (30, 25, "watch"),  # 1~2개월 -> 관찰
]


@dataclass
class CLVResult:
    """CLV 계산 결과."""

    customer_id: str
    total_revenue: Decimal
    order_count: int
    avg_order_value: Decimal
    purchase_frequency: Decimal  # 월당 주문 수
    lifespan_months: int
    clv: Decimal
    tier: str
    last_order_date: date | None


class CustomerLifetimeValueService:
    """고객 생애 가치 및 이탈 위험 평가 서비스."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._customer_repo = Repository("customers", tenant_id=tenant_id)
        self._order_repo = Repository("sales_orders", tenant_id=tenant_id)
        self._opp_repo = Repository("opportunities", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # BR-CRM-024: CLV 계산
    # ------------------------------------------------------------------

    def calculate_clv(self, customer_id: str) -> dict[str, Any]:
        """BR-CRM-024: 고객 생애 가치를 계산한다.

        방법론:
        1. sales_orders 컬렉션에서 docstatus=1(확정)인 주문 조회
        2. 총 매출, 주문 수, 첫/마지막 거래일 수집
        3. CLV = 평균 주문액 x 월 구매 빈도 x 고객 수명(월)

        Args:
            customer_id: 고객 ID

        Returns:
            CLVResult를 dict로 변환
        """
        orders = self._order_repo.find_many(
            {"customer_id": customer_id, "docstatus": 1},
            limit=10000,
        )

        if not orders:
            # 거래 이력 없음 -> 빈 결과
            logger.info("CLV 계산 건너뜀: 고객 '%s'의 확정 주문 없음", customer_id)
            return {
                "customer_id": customer_id,
                "total_revenue": 0.0,
                "order_count": 0,
                "avg_order_value": 0.0,
                "purchase_frequency": 0.0,
                "lifespan_months": 0,
                "clv": 0.0,
                "tier": "inactive",
                "last_order_date": None,
            }

        total_revenue = Decimal(0)
        order_dates: list[date] = []
        for order in orders:
            total_revenue += Decimal(str(order.get("grand_total", 0)))
            order_date = self._to_date(order.get("created_at") or order.get("order_date"))
            if order_date:
                order_dates.append(order_date)

        order_count = len(orders)
        avg_order_value = total_revenue / Decimal(order_count) if order_count > 0 else Decimal(0)

        # 고객 수명(월) — 첫 거래일부터 오늘까지
        first_order = min(order_dates) if order_dates else None
        last_order = max(order_dates) if order_dates else None
        today = datetime.now(tz=UTC).date()

        lifespan_days = (today - first_order).days if first_order else 0
        lifespan_months = max(1, lifespan_days // 30)

        # 월 구매 빈도
        purchase_frequency = Decimal(order_count) / Decimal(lifespan_months)

        # CLV = 평균 주문액 x 월 빈도 x 수명
        clv = (avg_order_value * purchase_frequency * Decimal(lifespan_months)).quantize(
            Decimal("0.01")
        )

        tier = self._classify_tier(clv)

        logger.info(
            "CLV 계산: 고객=%s, 주문=%d, 총매출=%s, CLV=%s, 등급=%s",
            customer_id,
            order_count,
            total_revenue,
            clv,
            tier,
        )

        return {
            "customer_id": customer_id,
            "total_revenue": float(total_revenue),
            "order_count": order_count,
            "avg_order_value": float(avg_order_value.quantize(Decimal("0.01"))),
            "purchase_frequency": float(purchase_frequency.quantize(Decimal("0.01"))),
            "lifespan_months": lifespan_months,
            "clv": float(clv),
            "tier": tier,
            "last_order_date": str(last_order) if last_order else None,
        }

    # ------------------------------------------------------------------
    # BR-CRM-025: 이탈 위험 점수
    # ------------------------------------------------------------------

    def assess_churn_risk(self, customer_id: str) -> dict[str, Any]:
        """BR-CRM-025: 최근 거래 갭 기반 이탈 위험을 평가한다.

        Args:
            customer_id: 고객 ID

        Returns:
            {"customer_id", "days_since_last_order", "risk_score", "risk_level", "last_order_date"}
        """
        orders = self._order_repo.find_many(
            {"customer_id": customer_id, "docstatus": 1},
            limit=10000,
        )

        if not orders:
            return {
                "customer_id": customer_id,
                "days_since_last_order": None,
                "risk_score": 0,
                "risk_level": "unknown",
                "last_order_date": None,
                "reason": "거래 이력 없음",
            }

        last_date: date | None = None
        for order in orders:
            order_date = self._to_date(order.get("created_at") or order.get("order_date"))
            if order_date and (last_date is None or order_date > last_date):
                last_date = order_date

        if last_date is None:
            return {
                "customer_id": customer_id,
                "days_since_last_order": None,
                "risk_score": 0,
                "risk_level": "unknown",
                "last_order_date": None,
                "reason": "주문 날짜 없음",
            }

        today = datetime.now(tz=UTC).date()
        gap_days = (today - last_date).days

        risk_score, risk_level = self._classify_churn_risk(gap_days)

        logger.info(
            "이탈 위험 평가: 고객=%s, 경과일=%d, 점수=%d, 등급=%s",
            customer_id,
            gap_days,
            risk_score,
            risk_level,
        )

        return {
            "customer_id": customer_id,
            "days_since_last_order": gap_days,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "last_order_date": str(last_date),
        }

    # ------------------------------------------------------------------
    # BR-CRM-026: 고객 세그먼트 기반 상위 N 집계
    # ------------------------------------------------------------------

    def get_top_customers_by_clv(self, limit: int = 10) -> list[dict[str, Any]]:
        """CLV 상위 N 고객 목록을 반환한다.

        Args:
            limit: 반환할 상위 고객 수

        Returns:
            CLV 내림차순 고객 목록
        """
        customers = self._customer_repo.find_many({}, limit=1000)

        results: list[dict[str, Any]] = []
        for customer in customers:
            cid = str(customer.get("_id", ""))
            if not cid:
                continue
            clv_result = self.calculate_clv(cid)
            if clv_result.get("order_count", 0) > 0:
                results.append(clv_result)

        results.sort(key=lambda x: float(x.get("clv", 0)), reverse=True)
        return results[:limit]

    def get_at_risk_customers(self, min_score: int = 50) -> list[dict[str, Any]]:
        """이탈 위험이 임계점 이상인 고객 목록을 반환한다.

        Args:
            min_score: 최소 위험 점수 (기본 50 = warning 이상)

        Returns:
            위험 점수 내림차순 고객 목록
        """
        customers = self._customer_repo.find_many({}, limit=1000)

        at_risk: list[dict[str, Any]] = []
        for customer in customers:
            cid = str(customer.get("_id", ""))
            if not cid:
                continue
            risk = self.assess_churn_risk(cid)
            if risk.get("risk_score", 0) >= min_score:
                at_risk.append(risk)

        at_risk.sort(key=lambda x: int(x.get("risk_score", 0)), reverse=True)
        return at_risk

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _classify_tier(self, clv: Decimal) -> str:
        """CLV 등급을 분류한다."""
        for threshold, tier in _CLV_TIERS:
            if clv >= threshold:
                return tier
        return "standard"

    def _classify_churn_risk(self, gap_days: int) -> tuple[int, str]:
        """최근 거래 갭에 따른 위험 점수와 등급을 반환한다."""
        for days, score, level in _CHURN_TIERS:
            if gap_days >= days:
                return score, level
        return 0, "healthy"

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
                return date.fromisoformat(value[:10])
            except ValueError:
                try:
                    return datetime.fromisoformat(value).date()
                except ValueError:
                    return None
        return None

    # ------------------------------------------------------------------
    # 고객 일괄 조회 API
    # ------------------------------------------------------------------

    def calculate_customer_summary(self, customer_id: str) -> dict[str, Any]:
        """CLV와 이탈 위험을 함께 반환한다.

        Args:
            customer_id: 고객 ID

        Returns:
            {"clv": {...}, "churn_risk": {...}}
        """
        customer = self._customer_repo.find_by_id(customer_id)
        if customer is None:
            raise_not_found(f"고객 '{customer_id}'을 찾을 수 없습니다")

        return {
            "customer_id": customer_id,
            "clv": self.calculate_clv(customer_id),
            "churn_risk": self.assess_churn_risk(customer_id),
        }
