"""공급업체 평가 서비스 — 납기/품질/가격 기반 자동 평가 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-BUY-006: 공급업체 평가 가중치 delivery(40%) + quality(35%) + price(25%)
- BR-BUY-012: 납기 점수 = 입고건수 / 발주건수 x 100
- BR-BUY-013: 품질 점수 = (입고건수 - 반품건수) / 입고건수 x 100
"""

from __future__ import annotations

import calendar
import logging
import re
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def _build_period_filter(evaluation_period: str) -> dict[str, str] | None:
    """평가 기간 문자열을 MongoDB 날짜 범위 필터로 변환한다.

    지원 형식: "YYYY-QN" (분기), "YYYY-MM" (월). 미매칭 시 None.
    """
    m = re.match(r"^(\d{4})-Q([1-4])$", evaluation_period)
    if m:
        year, quarter = int(m.group(1)), int(m.group(2))
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        last_day = calendar.monthrange(year, end_month)[1]
        return {
            "$gte": f"{year:04d}-{start_month:02d}-01",
            "$lte": f"{year:04d}-{end_month:02d}-{last_day:02d}",
        }

    m = re.match(r"^(\d{4})-(\d{2})$", evaluation_period)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        last_day = calendar.monthrange(year, month)[1]
        return {
            "$gte": f"{year:04d}-{month:02d}-01",
            "$lte": f"{year:04d}-{month:02d}-{last_day:02d}",
        }

    return None


# 평가 기준별 가중치 (합계 100)
_CRITERIA_WEIGHTS: dict[str, float] = {
    "delivery": 40.0,  # 납기 준수율
    "quality": 35.0,  # 품질 적합률
    "price": 25.0,  # 가격 경쟁력
}


class SupplierScorecardService:
    """공급업체 자동 평가 비즈니스 로직.

    입고 이력과 반품 이력을 기반으로 공급업체를 자동 평가한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._scorecard_repo = Repository("supplier_scorecards", tenant_id=tenant_id)
        self._receipt_repo = Repository("purchase_receipts", tenant_id=tenant_id)
        self._return_repo = Repository("purchase_returns", tenant_id=tenant_id)
        self._po_repo = Repository("purchase_orders", tenant_id=tenant_id)

    def evaluate_supplier(
        self,
        supplier_id: str,
        evaluation_period: str,
    ) -> dict[str, Any]:
        """BR-BUY-006: 공급업체 가중 평가 — delivery(40%)+quality(35%)+price(25%).

        Args:
            supplier_id: 공급업체 ID
            evaluation_period: 평가 기간 (예: "2026-Q1")

        Returns:
            평가 결과 (scorecard_id, total_score, criteria)
        """
        # 기간 필터 구성 (evaluation_period가 있으면 날짜 범위 적용)
        period_filter = _build_period_filter(evaluation_period)

        # 입고 이력 조회
        receipt_query: dict[str, Any] = {"supplier": supplier_id}
        if period_filter:
            receipt_query["posting_date"] = period_filter
        receipts = self._receipt_repo.find_many(receipt_query, limit=10000)

        # 반품 이력 조회
        return_query: dict[str, Any] = {"supplier": supplier_id}
        if period_filter:
            return_query["posting_date"] = period_filter
        returns = self._return_repo.find_many(return_query, limit=10000)

        # 발주 이력 조회
        order_query: dict[str, Any] = {"supplier_id": supplier_id}
        if period_filter:
            order_query["transaction_date"] = period_filter
        orders = self._po_repo.find_many(order_query, limit=10000)

        # 납기 준수율 계산
        delivery_score = self._calculate_delivery_score(orders, receipts)

        # 품질 적합률 계산
        quality_score = self._calculate_quality_score(receipts, returns)

        # 가격 경쟁력 계산 (입고 건수 기반 단순 점수)
        price_score = self._calculate_price_score(orders)

        # 가중 평균
        total_score = round(
            delivery_score * _CRITERIA_WEIGHTS["delivery"] / 100
            + quality_score * _CRITERIA_WEIGHTS["quality"] / 100
            + price_score * _CRITERIA_WEIGHTS["price"] / 100,
            2,
        )

        criteria = {
            "delivery": {"score": delivery_score, "weight": _CRITERIA_WEIGHTS["delivery"]},
            "quality": {"score": quality_score, "weight": _CRITERIA_WEIGHTS["quality"]},
            "price": {"score": price_score, "weight": _CRITERIA_WEIGHTS["price"]},
        }

        # 평가 저장
        ssc_id = generate_name("SSC", tenant_id=self._tenant_id)
        doc = {
            "_id": ssc_id,
            "supplier": supplier_id,
            "evaluation_period": evaluation_period,
            "total_score": total_score,
            "criteria": criteria,
            "tenant_id": self._tenant_id,
        }
        self._scorecard_repo.insert(doc)

        logger.info(
            "공급업체 평가: %s (업체: %s, 점수: %.2f)",
            ssc_id,
            supplier_id,
            total_score,
        )

        return {
            "scorecard_id": ssc_id,
            "supplier": supplier_id,
            "evaluation_period": evaluation_period,
            "total_score": total_score,
            "criteria": criteria,
        }

    @staticmethod
    def _calculate_delivery_score(
        orders: list[dict[str, Any]],
        receipts: list[dict[str, Any]],
    ) -> float:
        """BR-BUY-012: 납기 준수율 = 입고 건수 / 발주 건수 x 100."""
        if not orders:
            return 0.0
        receipt_count = len(receipts)
        order_count = len(orders)
        return min(round(receipt_count / order_count * 100, 2), 100.0)

    @staticmethod
    def _calculate_quality_score(
        receipts: list[dict[str, Any]],
        returns: list[dict[str, Any]],
    ) -> float:
        """BR-BUY-013: 품질 적합률 = (입고 건수 - 반품 건수) / 입고 건수 x 100."""
        if not receipts:
            return 0.0
        good_count = max(len(receipts) - len(returns), 0)
        return round(good_count / len(receipts) * 100, 2)

    @staticmethod
    def _calculate_price_score(orders: list[dict[str, Any]]) -> float:
        """가격 경쟁력: 발주 이력이 있으면 기본 70점, 없으면 0점."""
        if not orders:
            return 0.0
        return 70.0
