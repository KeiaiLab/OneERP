"""ABC 재고 분석 서비스 — 파레토 원칙 기반 품목 분류.

이론적 배경:
- 파레토 80/20 법칙: 20% 품목이 80% 가치를 차지
- ABC 3분류 (NetSuite/MRPeasy/Bizowie 베스트 프랙티스):
  - A 등급: 누적 가치 비율 ≤ 80% → 핵심 관리 품목
  - B 등급: 80% < 누적 가치 비율 ≤ 95% → 표준 관리 품목
  - C 등급: 95% < 누적 가치 비율 ≤ 100% → 경량 관리 품목

분석 기준 선택:
- by_value: 재고 가치(qty x valuation_rate) 기준 — 가장 일반적
- by_consumption: 출고 금액 기준 — 매출 기여도 분석에 적합
- by_qty: 수량 기준 — 보관 공간 최적화에 적합

L2 비즈니스 룰 매핑:
- BR-STK-016: 안전재고 차등 적용 (A 등급은 높은 서비스 수준 유지)
- BR-STK-017: 리오더 빈도 차등 (A 등급은 더 자주 점검)
- BR-STK-018: 순환재고조사 주기 차등 (A 등급은 매월, C 등급은 분기)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Literal

from oneerp_core.errors import raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 등급 임계값 (누적 비율 기준)
DEFAULT_A_THRESHOLD = Decimal("0.80")
DEFAULT_B_THRESHOLD = Decimal("0.95")

ClassificationBasis = Literal["by_value", "by_consumption", "by_qty"]


class ABCAnalysisService:
    """ABC 재고 분석(Pareto Classification) 비즈니스 로직.

    품목별 메트릭(가치/소비/수량)을 집계한 뒤, 누적 비율로
    A/B/C 등급을 부여하여 차등 관리 정책의 근거를 제공한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bin_repo = Repository("stock_bins", tenant_id=tenant_id)
        self._sle_repo = Repository("stock_ledger_entries", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def classify_items(
        self,
        *,
        basis: ClassificationBasis = "by_value",
        a_threshold: Decimal = DEFAULT_A_THRESHOLD,
        b_threshold: Decimal = DEFAULT_B_THRESHOLD,
        warehouse: str | None = None,
    ) -> dict[str, Any]:
        """전체 품목을 ABC 등급으로 분류한다.

        Args:
            basis: 분류 기준 (by_value | by_consumption | by_qty)
            a_threshold: A 등급 누적 비율 상한 (기본 0.80)
            b_threshold: B 등급 누적 비율 상한 (기본 0.95)
            warehouse: 특정 창고만 분석 (None이면 전체)

        Returns:
            {
                basis, total_metric, item_count,
                items: [{item_code, metric, share, cumulative_share, classification}],
                summary: {A: {count, value_share}, B: {...}, C: {...}}
            }

        Raises:
            OneERPError(422): 임계값이 0~1 범위를 벗어남
            OneERPError(422): a_threshold >= b_threshold
        """
        self._validate_thresholds(a_threshold, b_threshold)

        # 1. 메트릭 수집
        item_metrics = self._collect_metrics(basis=basis, warehouse=warehouse)

        if not item_metrics:
            return {
                "basis": basis,
                "total_metric": Decimal(0),
                "item_count": 0,
                "items": [],
                "summary": self._empty_summary(),
            }

        # 2. 정렬 (메트릭 내림차순)
        sorted_items = sorted(
            item_metrics.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )

        # 3. 합계 계산
        total_metric = sum((m for _, m in sorted_items), Decimal(0))

        if total_metric <= 0:
            return {
                "basis": basis,
                "total_metric": Decimal(0),
                "item_count": len(sorted_items),
                "items": [
                    {
                        "item_code": code,
                        "metric": metric,
                        "share": Decimal(0),
                        "cumulative_share": Decimal(0),
                        "classification": "C",
                    }
                    for code, metric in sorted_items
                ],
                "summary": self._empty_summary(),
            }

        # 4. 누적 비율 + 등급 부여
        # 표준 알고리즘: "이 품목 직전 누적이 임계 이하"이면 임계 이내 등급으로 분류
        # → 첫 번째 품목은 항상 A, 임계를 넘기 직전까지 같은 등급
        result_items: list[dict[str, Any]] = []
        cumulative = Decimal(0)
        summary: dict[str, dict[str, Any]] = {
            "A": {"count": 0, "value_share": Decimal(0)},
            "B": {"count": 0, "value_share": Decimal(0)},
            "C": {"count": 0, "value_share": Decimal(0)},
        }

        for code, metric in sorted_items:
            share = metric / total_metric
            prev_cumulative = cumulative
            cumulative += share
            classification = self._classify(
                cumulative_before=prev_cumulative,
                a_threshold=a_threshold,
                b_threshold=b_threshold,
            )

            summary[classification]["count"] += 1
            summary[classification]["value_share"] += share

            result_items.append(
                {
                    "item_code": code,
                    "metric": metric,
                    "share": share,
                    "cumulative_share": cumulative,
                    "classification": classification,
                }
            )

        logger.info(
            "ABC 분석 완료: 기준=%s, 전체 %d건 (A=%d, B=%d, C=%d)",
            basis,
            len(sorted_items),
            summary["A"]["count"],
            summary["B"]["count"],
            summary["C"]["count"],
        )

        return {
            "basis": basis,
            "total_metric": total_metric,
            "item_count": len(sorted_items),
            "items": result_items,
            "summary": summary,
        }

    def get_item_classification(
        self,
        item_code: str,
        *,
        basis: ClassificationBasis = "by_value",
        warehouse: str | None = None,
    ) -> dict[str, Any]:
        """단일 품목의 ABC 분류를 조회한다.

        전체 분류를 실행한 뒤 해당 품목 결과만 추출한다.

        Args:
            item_code: 품목 코드
            basis: 분류 기준
            warehouse: 특정 창고 (선택)

        Returns:
            {item_code, classification, share, cumulative_share, metric}
            품목이 메트릭에 포함되지 않으면 classification="C", metric=0 반환
        """
        result = self.classify_items(basis=basis, warehouse=warehouse)

        for item in result["items"]:
            if item["item_code"] == item_code:
                return {
                    "item_code": item_code,
                    "basis": basis,
                    "classification": item["classification"],
                    "metric": item["metric"],
                    "share": item["share"],
                    "cumulative_share": item["cumulative_share"],
                }

        return {
            "item_code": item_code,
            "basis": basis,
            "classification": "C",
            "metric": Decimal(0),
            "share": Decimal(0),
            "cumulative_share": Decimal(0),
        }

    # ------------------------------------------------------------------
    # 메트릭 수집
    # ------------------------------------------------------------------

    def _collect_metrics(
        self,
        *,
        basis: ClassificationBasis,
        warehouse: str | None,
    ) -> dict[str, Decimal]:
        """기준에 따라 품목별 메트릭을 집계한다.

        - by_value/by_qty: stock_bins에서 직접 집계
        - by_consumption: stock_ledger_entries에서 출고(qty<0) 합산
        """
        if basis == "by_consumption":
            return self._collect_consumption_metric(warehouse)

        # by_value / by_qty 모두 stock_bins 기반
        query: dict[str, Any] = {}
        if warehouse:
            query["warehouse"] = warehouse

        bins = self._bin_repo.find_many(query, limit=10000)
        metrics: dict[str, Decimal] = {}

        for b in bins:
            item_code = str(b.get("item_code", ""))
            if not item_code:
                continue

            qty = Decimal(str(b.get("current_qty", 0)))
            value = Decimal(str(b.get("current_value", 0)))

            metric = value if basis == "by_value" else qty  # by_value 또는 by_qty

            if metric <= 0:
                continue

            metrics[item_code] = metrics.get(item_code, Decimal(0)) + metric

        return metrics

    def _collect_consumption_metric(self, warehouse: str | None) -> dict[str, Decimal]:
        """SLE에서 출고 가치(qty_change<0) 합산.

        부호를 양수로 변환하여 누적한다 (소비량 = abs(qty_change) x rate).
        """
        query: dict[str, Any] = {}
        if warehouse:
            query["warehouse"] = warehouse

        sles = self._sle_repo.find_many(query, limit=50000)
        metrics: dict[str, Decimal] = {}

        for sle in sles:
            qty_change = Decimal(str(sle.get("qty_change", 0)))
            if qty_change >= 0:
                continue  # 입고는 제외

            item_code = str(sle.get("item_code", ""))
            if not item_code:
                continue

            rate = Decimal(str(sle.get("valuation_rate", 0)))
            consumption = abs(qty_change) * rate

            if consumption <= 0:
                continue

            metrics[item_code] = metrics.get(item_code, Decimal(0)) + consumption

        return metrics

    # ------------------------------------------------------------------
    # 분류/검증
    # ------------------------------------------------------------------

    def _classify(
        self,
        *,
        cumulative_before: Decimal,
        a_threshold: Decimal,
        b_threshold: Decimal,
    ) -> str:
        """직전 누적(cumulative_before) 기반 등급 부여.

        표준 알고리즘:
        - 직전 누적 < a_threshold → A (이 품목이 임계 안에서 시작)
        - a_threshold ≤ 직전 누적 < b_threshold → B
        - b_threshold ≤ 직전 누적 → C

        이렇게 하면 첫 번째 품목(누적 직전 0)은 항상 A로 분류된다.
        """
        if cumulative_before < a_threshold:
            return "A"
        if cumulative_before < b_threshold:
            return "B"
        return "C"

    def _validate_thresholds(self, a_threshold: Decimal, b_threshold: Decimal) -> None:
        """임계값 검증."""
        if a_threshold <= 0 or a_threshold >= 1:
            msg = f"A 등급 임계값은 0~1 범위여야 합니다: {a_threshold}"
            raise_unprocessable("ERR-STK-ABC-001", msg)
        if b_threshold <= 0 or b_threshold >= 1:
            msg = f"B 등급 임계값은 0~1 범위여야 합니다: {b_threshold}"
            raise_unprocessable("ERR-STK-ABC-002", msg)
        if a_threshold >= b_threshold:
            msg = f"A 임계값({a_threshold})은 B 임계값({b_threshold})보다 작아야 합니다"
            raise_unprocessable("ERR-STK-ABC-003", msg)

    def _empty_summary(self) -> dict[str, dict[str, Any]]:
        """빈 요약 구조."""
        return {
            "A": {"count": 0, "value_share": Decimal(0)},
            "B": {"count": 0, "value_share": Decimal(0)},
            "C": {"count": 0, "value_share": Decimal(0)},
        }
