"""데이터 집계 서비스 단위 테스트."""

from __future__ import annotations

from oneerp_analytics_app.services.data_aggregation_service import DataAggregationService


class TestDataAggregationService:
    """DataAggregationService 테스트."""

    def test_aggregate_revenue(self, mock_collection) -> None:
        """기간별 매출을 합산한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {"grand_total": 1000.0},
            {"grand_total": 2000.0},
        ]
        svc = DataAggregationService("T1")
        result = svc.aggregate_revenue("2026-Q1")
        assert result["revenue"] == 3000.0
        assert result["invoice_count"] == 2

    def test_aggregate_revenue_empty(self, mock_collection) -> None:
        """인보이스가 없으면 매출 0."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = []
        svc = DataAggregationService("T1")
        result = svc.aggregate_revenue("2026-Q1")
        assert result["revenue"] == 0.0
        assert result["invoice_count"] == 0

    def test_aggregate_inventory_value(self, mock_collection) -> None:
        """재고 수량 x 가격을 합산한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {"qty": 10, "valuation_rate": 100.0},
            {"qty": 5, "valuation_rate": 200.0},
        ]
        svc = DataAggregationService("T1")
        result = svc.aggregate_inventory_value()
        assert result["inventory_value"] == 2000.0

    def test_aggregate_receivables(self, mock_collection) -> None:
        """매출채권 미수금을 합산한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {"outstanding_amount": 500.0},
            {"outstanding_amount": 300.0},
        ]
        svc = DataAggregationService("T1")
        result = svc.aggregate_receivables()
        assert result["receivables"] == 800.0

    def test_collect_all_kpis(self, mock_collection) -> None:
        """4개 핵심 지표를 일괄 수집한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {
                "grand_total": 5000.0,
                "qty": 10,
                "valuation_rate": 100.0,
                "outstanding_amount": 200.0,
            },
        ]
        svc = DataAggregationService("T1")
        result = svc.collect_all_kpis("2026-Q1")
        assert "revenue" in result
        assert "inventory_value" in result
        assert "receivables" in result
        assert result["period"] == "2026-Q1"
