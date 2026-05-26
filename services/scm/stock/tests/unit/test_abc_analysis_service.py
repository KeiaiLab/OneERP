"""ABC 재고 분석 서비스(ABCAnalysisService) 단위 테스트.

classify_items, get_item_classification 메서드의
정상·예외·경계값 시나리오를 검증한다.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@contextmanager
def _service_context(
    *,
    bins: list[dict] | None = None,
    sles: list[dict] | None = None,
):
    """mock 컨텍스트와 서비스 인스턴스를 yield한다."""
    with patch(
        "oneerp_stock_app.services.abc_analysis_service.Repository",
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "stock_bins":
                repo.find_many.return_value = bins or []
            elif collection_name == "stock_ledger_entries":
                repo.find_many.return_value = sles or []

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.abc_analysis_service import ABCAnalysisService

        service = ABCAnalysisService(tenant_id="test-tenant")
        yield service, repos


# ======================================================================
# 정상 케이스 (by_value)
# ======================================================================


class TestABC분류_가치기준:
    """by_value 기준 ABC 분류."""

    def test_3등급_분류_파레토(self) -> None:
        """파레토 80/15/5 분포: A(20%, 80%), B(20%, 15%), C(60%, 5%)."""
        bins = [
            {"item_code": "A1", "current_qty": 1, "current_value": 800},  # 80%
            {"item_code": "B1", "current_qty": 1, "current_value": 150},  # 15%
            {"item_code": "C1", "current_qty": 1, "current_value": 30},  # 3%
            {"item_code": "C2", "current_qty": 1, "current_value": 20},  # 2%
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_value")

            assert result["item_count"] == 4
            assert result["total_metric"] == Decimal(1000)

            # 정렬 후 첫 번째는 A1
            items = result["items"]
            assert items[0]["item_code"] == "A1"
            assert items[0]["classification"] == "A"
            assert items[0]["share"] == Decimal("0.8")

            # B1: 누적 0.95 → B
            assert items[1]["item_code"] == "B1"
            assert items[1]["classification"] == "B"

            # C1, C2: 누적 > 0.95 → C
            assert items[2]["classification"] == "C"
            assert items[3]["classification"] == "C"

            summary = result["summary"]
            assert summary["A"]["count"] == 1
            assert summary["B"]["count"] == 1
            assert summary["C"]["count"] == 2

    def test_단일_품목_A등급(self) -> None:
        """품목 1개면 모든 가치를 차지하므로 A 등급."""
        bins = [{"item_code": "ONLY", "current_qty": 1, "current_value": 1000}]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_value")

            assert result["item_count"] == 1
            assert result["items"][0]["classification"] == "A"
            assert result["summary"]["A"]["count"] == 1

    def test_정렬_내림차순(self) -> None:
        """가치 큰 순서대로 정렬되어야 한다."""
        bins = [
            {"item_code": "X", "current_qty": 1, "current_value": 100},
            {"item_code": "Y", "current_qty": 1, "current_value": 500},
            {"item_code": "Z", "current_qty": 1, "current_value": 300},
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_value")

            codes = [item["item_code"] for item in result["items"]]
            assert codes == ["Y", "Z", "X"]

    def test_가치_0인_품목_제외(self) -> None:
        """current_value=0인 품목은 분석에서 제외된다."""
        bins = [
            {"item_code": "A", "current_qty": 1, "current_value": 100},
            {"item_code": "ZERO", "current_qty": 0, "current_value": 0},
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_value")
            assert result["item_count"] == 1
            assert result["items"][0]["item_code"] == "A"


# ======================================================================
# 정상 케이스 (by_consumption)
# ======================================================================


class TestABC분류_소비기준:
    """by_consumption 기준 — SLE 출고 합산."""

    def test_출고가치_기준_분류(self) -> None:
        """qty_change<0인 SLE만 합산 (출고 가치)."""
        sles = [
            # 입고는 무시
            {"item_code": "A", "qty_change": 100, "valuation_rate": 10},
            # 출고
            {"item_code": "A", "qty_change": -50, "valuation_rate": 10},  # 500
            {"item_code": "B", "qty_change": -30, "valuation_rate": 5},  # 150
        ]

        with _service_context(sles=sles) as (service, _repos):
            result = service.classify_items(basis="by_consumption")

            assert result["item_count"] == 2
            assert result["total_metric"] == Decimal(650)
            # A가 더 큰 출고 가치
            assert result["items"][0]["item_code"] == "A"
            assert result["items"][0]["metric"] == Decimal(500)


# ======================================================================
# 정상 케이스 (by_qty)
# ======================================================================


class TestABC분류_수량기준:
    """by_qty 기준 — 수량으로 분류."""

    def test_수량_기준_정렬(self) -> None:
        """current_qty 기준 내림차순 정렬."""
        bins = [
            {"item_code": "SMALL", "current_qty": 10, "current_value": 1000000},
            {"item_code": "LARGE", "current_qty": 1000, "current_value": 1},
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_qty")
            assert result["items"][0]["item_code"] == "LARGE"


# ======================================================================
# 단일 품목 조회
# ======================================================================


class Test단일품목조회:
    """get_item_classification — 특정 품목의 등급 조회."""

    def test_품목_등급_조회(self) -> None:
        """기존 분류 결과에서 단일 품목 추출."""
        bins = [
            {"item_code": "TOP", "current_qty": 1, "current_value": 900},
            {"item_code": "MID", "current_qty": 1, "current_value": 100},
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.get_item_classification("TOP")
            assert result["classification"] == "A"
            assert result["item_code"] == "TOP"

    def test_미등록_품목_C등급_반환(self) -> None:
        """메트릭에 없는 품목은 C 등급, metric=0."""
        bins = [{"item_code": "OTHER", "current_qty": 1, "current_value": 100}]

        with _service_context(bins=bins) as (service, _repos):
            result = service.get_item_classification("MISSING")
            assert result["classification"] == "C"
            assert result["metric"] == Decimal(0)


# ======================================================================
# 예외 케이스
# ======================================================================


class TestABC분류_예외:
    """임계값 검증."""

    def test_a_threshold_범위초과_422(self) -> None:
        """a_threshold가 1 이상이면 422."""
        with _service_context(bins=[]) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.classify_items(a_threshold=Decimal("1.5"))
            assert exc.value.error == "ERR-STK-ABC-001"

    def test_b_threshold_0이하_422(self) -> None:
        """b_threshold가 0이면 422."""
        with _service_context(bins=[]) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.classify_items(b_threshold=Decimal(0))
            assert exc.value.error == "ERR-STK-ABC-002"

    def test_a_threshold_b보다_큼_422(self) -> None:
        """a_threshold >= b_threshold이면 422."""
        with _service_context(bins=[]) as (service, _repos):
            with pytest.raises(OneERPError) as exc:
                service.classify_items(
                    a_threshold=Decimal("0.95"),
                    b_threshold=Decimal("0.80"),
                )
            assert exc.value.error == "ERR-STK-ABC-003"


# ======================================================================
# 경계값
# ======================================================================


class TestABC분류_경계값:
    """경계 시나리오."""

    def test_빈_데이터_처리(self) -> None:
        """stock_bins가 비어있으면 빈 결과."""
        with _service_context(bins=[]) as (service, _repos):
            result = service.classify_items()
            assert result["item_count"] == 0
            assert result["total_metric"] == Decimal(0)
            assert result["items"] == []
            assert result["summary"]["A"]["count"] == 0

    def test_total_metric_0이면_C로_표시(self) -> None:
        """모든 메트릭이 0이면 분류 불가, 모두 C."""
        # 가치 0인 품목만 → 메트릭 수집 단계에서 제외됨
        bins = [{"item_code": "X", "current_qty": 1, "current_value": 0}]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(basis="by_value")
            # value=0은 _collect_metrics에서 필터링되어 빈 결과
            assert result["item_count"] == 0

    def test_커스텀_임계값(self) -> None:
        """임계값을 70/90으로 변경한 분류."""
        bins = [
            {"item_code": "A1", "current_qty": 1, "current_value": 700},  # 70% A
            {"item_code": "A2", "current_qty": 1, "current_value": 200},  # 누적 90% B
            {"item_code": "C1", "current_qty": 1, "current_value": 100},  # 누적 100% C
        ]

        with _service_context(bins=bins) as (service, _repos):
            result = service.classify_items(
                a_threshold=Decimal("0.70"),
                b_threshold=Decimal("0.90"),
            )
            assert result["items"][0]["classification"] == "A"
            assert result["items"][1]["classification"] == "B"
            assert result["items"][2]["classification"] == "C"
